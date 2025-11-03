#!/usr/bin/env python3
"""
Faster Whisper STT Service
High-performance speech-to-text service with streaming support and end-of-utterance detection
Modular architecture with client-configurable parameters
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import (
    SERVICE_CONFIG,
    SessionConfig,
    AudioConfig,
    VADConfig,
    TranscriptionConfig
)
from audio_utils import AudioConverter
from vad_processor import AudioBuffer
from transcription import TranscriptionEngine

# Configure logging
logging.basicConfig(
    level=getattr(logging, SERVICE_CONFIG.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Faster Whisper STT Service",
    version="2.0.0",
    description="Configurable speech-to-text service with real-time streaming"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global transcription engine
transcription_engine: Optional[TranscriptionEngine] = None


class StreamingSession:
    """Manages a streaming transcription session"""
    
    def __init__(
        self,
        websocket: WebSocket,
        session_config: SessionConfig
    ):
        self.websocket = websocket
        self.config = session_config
        
        # Initialize components
        self.audio_converter = AudioConverter(session_config.audio)
        self.audio_buffer = AudioBuffer(session_config.vad, session_config.audio)
        
        # State
        self.is_active = True
        self.last_partial_text = ""
        self.partial_task: Optional[asyncio.Task] = None
        
        logger.info(f"Session created with config: {session_config.model_dump()}")
    
    async def start(self):
        """Start the session"""
        # Start partial transcription task if enabled
        if self.config.transcription.enable_partial_transcripts:
            self.partial_task = asyncio.create_task(self._partial_transcription_loop())
    
    async def stop(self):
        """Stop the session"""
        self.is_active = False
        if self.partial_task:
            self.partial_task.cancel()
            try:
                await self.partial_task
            except asyncio.CancelledError:
                pass
    
    async def process_audio(self, audio_bytes: bytes):
        """Process incoming audio chunk"""
        try:
            # Convert audio to standard format (PCM16, mono, 16kHz)
            normalized_audio = self.audio_converter.normalize_audio(audio_bytes)
            
            # Run VAD
            vad_result = self.audio_buffer.add_audio(normalized_audio)
            
            # Send status updates
            if vad_result.has_speech:
                await self.websocket.send_json({
                    "type": "status",
                    "is_speaking": vad_result.is_speaking,
                    "speech_duration": vad_result.speech_duration
                })
            
            # Handle end of utterance
            if vad_result.end_of_utterance:
                await self._handle_end_of_utterance(vad_result.audio_for_transcription)
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            await self.send_error(str(e))
    
    async def _handle_end_of_utterance(self, audio_data: bytes):
        """Handle end of utterance - perform final transcription"""
        try:
            # Convert to numpy
            audio_np = self.audio_converter.to_numpy(audio_data)
            
            # Transcribe
            result = transcription_engine.transcribe(
                audio_np,
                self.config.transcription
            )
            
            # Send final transcription
            await self.websocket.send_json({
                "type": "final",
                **result.to_dict()
            })
            
            # Send end of utterance event
            await self.websocket.send_json({
                "type": "end_of_utterance"
            })
            
            # Reset state
            self.last_partial_text = ""
            
        except Exception as e:
            logger.error(f"Final transcription error: {e}")
            await self.send_error(f"Transcription failed: {e}")
    
    async def _partial_transcription_loop(self):
        """Periodically send partial transcriptions"""
        try:
            while self.is_active:
                await asyncio.sleep(self.config.transcription.partial_interval)
                
                if self.audio_buffer.is_speaking:
                    audio_data = self.audio_buffer.get_accumulated_audio()
                    
                    if audio_data:
                        try:
                            # Convert to numpy
                            audio_np = self.audio_converter.to_numpy(audio_data)
                            
                            # Transcribe
                            result = transcription_engine.transcribe(
                                audio_np,
                                self.config.transcription
                            )
                            
                            # Only send if text changed
                            if result.text and result.text != self.last_partial_text:
                                self.last_partial_text = result.text
                                
                                await self.websocket.send_json({
                                    "type": "partial",
                                    "text": result.text,
                                    "is_speaking": True,
                                    "speech_duration": self.audio_buffer._get_speech_duration()
                                })
                                
                        except Exception as e:
                            logger.error(f"Partial transcription error: {e}")
                            
        except asyncio.CancelledError:
            pass
    
    async def handle_control_message(self, message: Dict[str, Any]):
        """Handle control messages from client"""
        msg_type = message.get("type")
        
        if msg_type == "reset":
            self.audio_buffer.reset()
            self.last_partial_text = ""
            await self.websocket.send_json({
                "type": "status",
                "message": "Buffer reset"
            })
            
        elif msg_type == "force_end":
            # Force end current utterance
            audio_data = self.audio_buffer.force_end_utterance()
            if audio_data:
                await self._handle_end_of_utterance(audio_data)
                
        elif msg_type == "get_stats":
            stats = self.audio_buffer.get_stats()
            await self.websocket.send_json({
                "type": "stats",
                **stats
            })
            
        else:
            logger.warning(f"Unknown control message type: {msg_type}")
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        try:
            await self.websocket.send_json({
                "type": "error",
                "message": error_message
            })
        except Exception as e:
            logger.error(f"Failed to send error: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global transcription_engine
    
    logger.info("=" * 60)
    logger.info("Faster Whisper STT Service v2.0.0")
    logger.info("=" * 60)
    
    try:
        # Initialize transcription engine
        transcription_engine = TranscriptionEngine(SERVICE_CONFIG)
        logger.info("Service ready!")
        logger.info(f"Listening on {SERVICE_CONFIG.host}:{SERVICE_CONFIG.port}")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_info = transcription_engine.get_model_info() if transcription_engine else {}
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        **model_info
    }


@app.get("/config/defaults")
async def get_default_config():
    """Get default configuration"""
    return SessionConfig().model_dump()


@app.post("/transcribe")
async def transcribe_file(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    beam_size: int = 5
):
    """
    Simple transcription endpoint for file upload
    
    Args:
        file: Audio file
        language: Language code (optional, auto-detect if None)
        beam_size: Beam size for decoding
    """
    try:
        # Read audio file
        audio_bytes = await file.read()
        
        # Use default audio config
        audio_config = AudioConfig()
        audio_converter = AudioConverter(audio_config)
        
        # Normalize audio
        normalized_audio = audio_converter.normalize_audio(audio_bytes)
        audio_np = audio_converter.to_numpy(normalized_audio)
        
        # Create transcription config
        trans_config = TranscriptionConfig(
            language=language,
            beam_size=beam_size
        )
        
        # Transcribe
        result = transcription_engine.transcribe(audio_np, trans_config)
        
        return JSONResponse(content={
            "success": True,
            **result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    Real-time streaming STT endpoint
    
    Protocol:
    1. Client connects
    2. Client sends JSON config message (optional): 
       {"type": "config", "audio": {...}, "vad": {...}, "transcription": {...}}
    3. Client sends binary audio chunks
    4. Server sends JSON messages:
       - {"type": "partial", "text": "...", "is_speaking": true}
       - {"type": "final", "text": "...", "segments": [...]}
       - {"type": "end_of_utterance"}
       - {"type": "status", "is_speaking": true/false}
       - {"type": "error", "message": "..."}
    5. Client can send control messages:
       - {"type": "reset"} - Reset buffer
       - {"type": "force_end"} - Force end current utterance
       - {"type": "get_stats"} - Get buffer stats
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    session: Optional[StreamingSession] = None
    session_config = SessionConfig()  # Default config
    config_received = False
    
    try:
        while True:
            # Receive data
            data = await websocket.receive()
            
            if "text" in data:
                # JSON message
                try:
                    message = json.loads(data["text"])
                    msg_type = message.get("type")
                    
                    if msg_type == "config":
                        # Configuration message
                        if not config_received:
                            try:
                                # Parse configuration
                                if "audio" in message:
                                    session_config.audio = AudioConfig(**message["audio"])
                                if "vad" in message:
                                    session_config.vad = VADConfig(**message["vad"])
                                if "transcription" in message:
                                    session_config.transcription = TranscriptionConfig(
                                        **message["transcription"]
                                    )
                                
                                # Create session with config
                                session = StreamingSession(websocket, session_config)
                                await session.start()
                                config_received = True
                                
                                await websocket.send_json({
                                    "type": "ready",
                                    "message": "Session configured and ready",
                                    "config": session_config.model_dump()
                                })
                                
                                logger.info("Session configured by client")
                                
                            except Exception as e:
                                logger.error(f"Config parsing error: {e}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Invalid configuration: {e}"
                                })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Configuration already set"
                            })
                    
                    elif msg_type in ["reset", "force_end", "get_stats"]:
                        # Control messages
                        if not session:
                            # Create default session if not configured yet
                            session = StreamingSession(websocket, session_config)
                            await session.start()
                            config_received = True
                        
                        await session.handle_control_message(message)
                    
                    else:
                        logger.warning(f"Unknown message type: {msg_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
            
            elif "bytes" in data:
                # Audio data
                audio_bytes = data["bytes"]
                
                # Create default session if not configured yet
                if not session:
                    session = StreamingSession(websocket, session_config)
                    await session.start()
                    config_received = True
                
                # Process audio
                await session.process_audio(audio_bytes)
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if session:
            await session.stop()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=SERVICE_CONFIG.host,
        port=SERVICE_CONFIG.port,
        log_level=SERVICE_CONFIG.log_level,
        access_log=True
    )
