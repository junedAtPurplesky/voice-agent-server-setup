#!/usr/bin/env python3
"""
Speechmatics-compatible STT Service
High-performance speech-to-text service with full Speechmatics API compatibility
"""

import asyncio
import json
import logging
import time
import base64
from typing import Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException, Path, Query, Header
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
from auth import auth_manager, initialize_auth, get_api_key, require_auth
from routes import router as api_router, set_transcription_engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, SERVICE_CONFIG.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Speechmatics-Compatible STT Service",
    version="2.0.0",
    description="Speechmatics-compatible speech-to-text service with real-time streaming"
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
    """Manages a streaming transcription session (Speechmatics-compatible)"""
    
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
        self.session_id = f"realtime_{int(time.time())}"
        
        logger.info(f"Session created: {self.session_id}")
    
    async def start(self):
        """Start the session"""
        # Send session started message (Speechmatics-style)
        await self.websocket.send_json({
            "message": "SessionStarted",
            "session_id": self.session_id
        })
        
        # Start partial transcription task if enabled
        if self.config.transcription.enable_partials:
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
            
            # Send status updates (Speechmatics-style)
            if vad_result.has_speech:
                await self.websocket.send_json({
                    "message": "AudioAdded",
                    "is_speaking": vad_result.is_speaking
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
            
            # Send final transcription (Speechmatics-style)
            speechmatics_result = result.to_speechmatics_format(
                self.config.transcription.output_format
            )
            
            await self.websocket.send_json({
                "message": "AddTranscript",
                "results": speechmatics_result.get("results", []),
                "language": result.language
            })
            
            # Send end of utterance event
            await self.websocket.send_json({
                "message": "EndOfTranscript"
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
                await asyncio.sleep(0.5)  # Check every 500ms
                
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
                                
                                # Send partial transcript (Speechmatics-style)
                                speechmatics_result = result.to_speechmatics_format(
                                    self.config.transcription.output_format
                                )
                                
                                await self.websocket.send_json({
                                    "message": "AddPartialTranscript",
                                    "results": speechmatics_result.get("results", []),
                                    "language": result.language
                                })
                                
                        except Exception as e:
                            logger.error(f"Partial transcription error: {e}")
                            
        except asyncio.CancelledError:
            pass
    
    async def handle_control_message(self, message: Dict[str, Any]):
        """Handle control messages from client"""
        msg_type = message.get("message")
        
        if msg_type == "ResetSession":
            self.audio_buffer.reset()
            self.last_partial_text = ""
            await self.websocket.send_json({
                "message": "SessionReset"
            })
            
        elif msg_type == "EndOfStream":
            # Force end current utterance
            audio_data = self.audio_buffer.force_end_utterance()
            if audio_data:
                await self._handle_end_of_utterance(audio_data)
            
        elif msg_type == "GetStatus":
            stats = self.audio_buffer.get_stats()
            await self.websocket.send_json({
                "message": "Status",
                **stats
            })
            
        else:
            logger.warning(f"Unknown control message type: {msg_type}")
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        try:
            await self.websocket.send_json({
                "message": "Error",
                "error": error_message
            })
        except Exception as e:
            logger.error(f"Failed to send error: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global transcription_engine
    
    logger.info("=" * 60)
    logger.info("Speechmatics-Compatible STT Service v2.0.0")
    logger.info("=" * 60)
    
    try:
        # Initialize authentication first
        initialize_auth(
            require_auth=SERVICE_CONFIG.require_auth,
            api_keys=SERVICE_CONFIG.api_keys if SERVICE_CONFIG.api_keys else None
        )
        
        # Initialize transcription engine
        transcription_engine = TranscriptionEngine(SERVICE_CONFIG)
        set_transcription_engine(transcription_engine)
        
        # Include API routes
        app.include_router(api_router)
        
        logger.info("Service ready!")
        logger.info(f"Listening on {SERVICE_CONFIG.host}:{SERVICE_CONFIG.port}")
        if SERVICE_CONFIG.require_auth:
            logger.info(f"🔒 Authentication: REQUIRED ({len(SERVICE_CONFIG.api_keys)} API key(s) configured)")
        else:
            logger.info("🔓 Authentication: OPTIONAL (disabled)")
        
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
        "service": "Speechmatics-Compatible STT",
        **model_info
    }


@app.get("/v1/config")
async def get_config(authorization: Optional[str] = Header(None)):
    """Get service configuration"""
    return {
        "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ko"],
        "output_formats": ["json", "text"],
        "features": {
            "partials": True,
            "realtime": True,
            "batch": True
        }
    }


@app.websocket("/v1/realtime")
async def websocket_realtime(websocket: WebSocket):
    """
    Real-time streaming STT endpoint (Speechmatics-compatible)
    
    Protocol:
    1. Client connects
    2. Client sends StartRecognition message:
       {"message": "StartRecognition", "config": {...}}
    3. Client sends AddAudio messages with base64 audio:
       {"message": "AddAudio", "audio": "base64..."}
    4. Server sends transcriptions:
       - {"message": "AddPartialTranscript", "results": [...]}
       - {"message": "AddTranscript", "results": [...]}
       - {"message": "EndOfTranscript"}
    5. Client can send control messages:
       - {"message": "ResetSession"}
       - {"message": "EndOfStream"}
       - {"message": "GetStatus"}
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
                    msg_type = message.get("message")
                    
                    if msg_type == "StartRecognition":
                        # Configuration message
                        if not config_received:
                            try:
                                config = message.get("config", {})
                                
                                # Parse configuration
                                if "language" in config:
                                    session_config.transcription.language = config["language"]
                                if "output_format" in config:
                                    session_config.transcription.output_format = config["output_format"]
                                if "enable_partials" in config:
                                    session_config.transcription.enable_partials = config["enable_partials"]
                                if "max_delay" in config:
                                    session_config.transcription.max_delay = config["max_delay"]
                                
                                # Audio config defaults
                                session_config.audio = AudioConfig()
                                
                                # VAD config defaults
                                session_config.vad = VADConfig()
                                
                                # Create session with config
                                session = StreamingSession(websocket, session_config)
                                await session.start()
                                config_received = True
                                
                                logger.info("Session configured by client")
                                
                            except Exception as e:
                                logger.error(f"Config parsing error: {e}")
                                await websocket.send_json({
                                    "message": "Error",
                                    "error": f"Invalid configuration: {e}"
                                })
                        else:
                            await websocket.send_json({
                                "message": "Error",
                                "error": "Configuration already set"
                            })
                    
                    elif msg_type == "AddAudio":
                        # Audio data (base64 encoded)
                        if not session:
                            # Create default session if not configured yet
                            session = StreamingSession(websocket, session_config)
                            await session.start()
                            config_received = True
                        
                        audio_b64 = message.get("audio", "")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            await session.process_audio(audio_bytes)
                    
                    elif msg_type in ["ResetSession", "EndOfStream", "GetStatus"]:
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
                        "message": "Error",
                        "error": "Invalid JSON format"
                    })
            
            elif "bytes" in data:
                # Binary audio data
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
