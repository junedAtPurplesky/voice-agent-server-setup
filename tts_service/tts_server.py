#!/usr/bin/env python3
"""
CosyVoice2 TTS Service
High-performance text-to-speech service with streaming support
Production-ready with ElevenLabs-style configurations
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from config import (
    SERVICE_CONFIG,
    SessionConfig,
    AudioConfig,
    VoiceConfig,
    StreamingConfig,
    SynthesisConfig,
    TextProcessingConfig
)
from audio_utils import AudioConverter
from text_processor import TextBuffer, StreamingSentenceIterator
from synthesis import SynthesisEngine

# Configure logging
logging.basicConfig(
    level=getattr(logging, SERVICE_CONFIG.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="CosyVoice2 TTS Service",
    version="1.0.0",
    description="Production-ready text-to-speech service with real-time streaming and ElevenLabs-style configurations"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global synthesis engine
synthesis_engine: Optional[SynthesisEngine] = None


class TTSRequest(BaseModel):
    """HTTP TTS request model"""
    text: str
    voice_config: Optional[VoiceConfig] = None
    audio_config: Optional[AudioConfig] = None
    synthesis_config: Optional[SynthesisConfig] = None


class StreamingSession:
    """Manages a streaming TTS session"""
    
    def __init__(
        self,
        websocket: WebSocket,
        session_config: SessionConfig
    ):
        self.websocket = websocket
        self.config = session_config
        
        # Initialize components
        self.audio_converter = AudioConverter(session_config.audio)
        self.text_buffer = TextBuffer(
            session_config.streaming,
            session_config.text_processing
        )
        
        # State
        self.is_active = True
        self.total_chars_processed = 0
        self.total_audio_duration = 0.0
        
        logger.info(f"Streaming session created with config: {session_config.model_dump()}")
    
    async def start(self):
        """Start the session"""
        await self.websocket.send_json({
            "type": "session_started",
            "message": "Streaming session ready"
        })
    
    async def stop(self):
        """Stop the session"""
        self.is_active = False
        
        # Flush any remaining text
        if self.text_buffer.has_data():
            await self._process_buffered_text()
    
    async def process_text(self, text: str):
        """
        Process incoming text chunk
        
        Args:
            text: Text chunk to synthesize
        """
        try:
            if len(text) > SERVICE_CONFIG.max_text_length:
                await self.send_error(f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)")
                return
            
            # Add to buffer
            ready_sentences = self.text_buffer.add_text(text)
            
            # Synthesize if threshold reached
            if ready_sentences:
                await self._synthesize_sentences(ready_sentences)
                
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            await self.send_error(str(e))
    
    async def flush(self):
        """Force flush buffered text"""
        try:
            await self._process_buffered_text()
            
            await self.websocket.send_json({
                "type": "flush_complete",
                "message": "All buffered text synthesized"
            })
            
        except Exception as e:
            logger.error(f"Flush error: {e}")
            await self.send_error(str(e))
    
    async def _process_buffered_text(self):
        """Process all buffered text"""
        sentences = self.text_buffer.flush()
        if sentences:
            await self._synthesize_sentences(sentences)
    
    async def _synthesize_sentences(self, sentences: list):
        """
        Synthesize a batch of sentences
        
        Args:
            sentences: List of sentences to synthesize
        """
        try:
            # Combine sentences
            text = " ".join(sentences)
            self.total_chars_processed += len(text)
            
            # Send processing notification
            await self.websocket.send_json({
                "type": "synthesis_start",
                "text": text,
                "char_count": len(text)
            })
            
            if self.config.streaming.enabled:
                # Streaming synthesis
                await self._streaming_synthesis(text)
            else:
                # Non-streaming synthesis
                await self._batch_synthesis(text)
                
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            await self.send_error(f"Synthesis failed: {e}")
    
    async def _streaming_synthesis(self, text: str):
        """Streaming synthesis with chunked output"""
        try:
            chunk_count = 0
            start_time = time.time()
            
            # Stream audio chunks
            for audio_chunk in synthesis_engine.synthesize_streaming(
                text,
                self.config.voice,
                self.config.synthesis,
                chunk_size=self.config.streaming.chunk_size
            ):
                # Convert audio
                audio_bytes = self.audio_converter.convert_audio(
                    audio_chunk,
                    24000  # CosyVoice2 sample rate
                )
                
                # Send audio chunk
                await self.websocket.send_bytes(audio_bytes)
                chunk_count += 1
                
                # Small delay for buffer management
                if self.config.streaming.optimize_streaming_latency < 3:
                    await asyncio.sleep(0.001)
            
            processing_time = time.time() - start_time
            
            # Send completion metadata
            await self.websocket.send_json({
                "type": "audio_complete",
                "text": text,
                "chunks_sent": chunk_count,
                "processing_time": processing_time
            })
            
        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}")
            raise
    
    async def _batch_synthesis(self, text: str):
        """Non-streaming synthesis (full audio at once)"""
        try:
            # Synthesize
            result = synthesis_engine.synthesize(
                text,
                self.config.voice,
                self.config.synthesis
            )
            
            self.total_audio_duration += result.audio_duration
            
            # Convert audio
            audio_bytes = self.audio_converter.convert_audio(
                result.audio,
                result.sample_rate
            )
            
            # Send metadata first
            await self.websocket.send_json({
                "type": "audio_start",
                **result.to_dict()
            })
            
            # Send audio
            await self.websocket.send_bytes(audio_bytes)
            
            # Send completion
            await self.websocket.send_json({
                "type": "audio_complete",
                "text": text
            })
            
        except Exception as e:
            logger.error(f"Batch synthesis error: {e}")
            raise
    
    async def handle_control_message(self, message: Dict[str, Any]):
        """Handle control messages from client"""
        msg_type = message.get("type")
        
        if msg_type == "flush":
            # Flush buffered text
            await self.flush()
            
        elif msg_type == "reset":
            # Reset buffer
            self.text_buffer.reset()
            await self.websocket.send_json({
                "type": "status",
                "message": "Buffer reset"
            })
            
        elif msg_type == "get_stats":
            # Get statistics
            stats = self.get_stats()
            await self.websocket.send_json({
                "type": "stats",
                **stats
            })
            
        else:
            logger.warning(f"Unknown control message type: {msg_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        buffer_stats = self.text_buffer.get_stats()
        
        return {
            "total_chars_processed": self.total_chars_processed,
            "total_audio_duration": self.total_audio_duration,
            **buffer_stats
        }
    
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
    global synthesis_engine
    
    logger.info("=" * 60)
    logger.info("CosyVoice2 TTS Service v1.0.0")
    logger.info("=" * 60)
    
    try:
        # Initialize synthesis engine
        synthesis_engine = SynthesisEngine(SERVICE_CONFIG)
        logger.info("Service ready!")
        logger.info(f"Listening on {SERVICE_CONFIG.host}:{SERVICE_CONFIG.port}")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_info = synthesis_engine.get_model_info() if synthesis_engine else {}
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "CosyVoice2 TTS",
        **model_info
    }


@app.get("/config/defaults")
async def get_default_config():
    """Get default configuration"""
    return SessionConfig().model_dump()


@app.get("/voices")
async def list_voices():
    """
    List available voices
    
    Returns:
        List of available voice configurations
    """
    if not synthesis_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    voices = synthesis_engine.list_voices()
    
    return {
        "voices": voices,
        "count": len(voices)
    }


@app.post("/synthesize")
async def synthesize_text(request: TTSRequest):
    """
    Simple TTS endpoint for text synthesis
    
    Args:
        request: TTS request with text and optional configurations
    
    Returns:
        JSON response with audio data (base64) and metadata
    """
    try:
        if not synthesis_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Validate text length
        if len(request.text) > SERVICE_CONFIG.max_text_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)"
            )
        
        # Use provided configs or defaults
        voice_config = request.voice_config or VoiceConfig()
        audio_config = request.audio_config or AudioConfig()
        synthesis_config = request.synthesis_config or SynthesisConfig()
        
        # Synthesize
        result = synthesis_engine.synthesize(
            request.text,
            voice_config,
            synthesis_config
        )
        
        # Convert audio
        audio_converter = AudioConverter(audio_config)
        audio_bytes = audio_converter.convert_audio(
            result.audio,
            result.sample_rate
        )
        
        # Encode to base64 for JSON response
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return JSONResponse(content={
            "success": True,
            "audio_base64": audio_base64,
            "audio_format": audio_config.encoding,
            **result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/stream")
async def synthesize_stream(request: TTSRequest):
    """
    Streaming TTS endpoint - returns audio as streaming response
    
    Args:
        request: TTS request with text and optional configurations
    
    Returns:
        Streaming audio response
    """
    try:
        if not synthesis_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        if len(request.text) > SERVICE_CONFIG.max_text_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)"
            )
        
        voice_config = request.voice_config or VoiceConfig()
        audio_config = request.audio_config or AudioConfig()
        synthesis_config = request.synthesis_config or SynthesisConfig()
        
        # Create audio converter
        audio_converter = AudioConverter(audio_config)
        
        async def generate_audio():
            """Generator for streaming audio"""
            for audio_chunk in synthesis_engine.synthesize_streaming(
                request.text,
                voice_config,
                synthesis_config,
                chunk_size=1024
            ):
                # Convert chunk
                audio_bytes = audio_converter.convert_audio(
                    audio_chunk,
                    24000
                )
                yield audio_bytes
        
        return StreamingResponse(
            generate_audio(),
            media_type=f"audio/{audio_config.encoding}"
        )
        
    except Exception as e:
        logger.error(f"Streaming synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    Real-time streaming TTS endpoint via WebSocket
    
    Protocol:
    1. Client connects
    2. Client sends JSON config message (optional):
       {"type": "config", "audio": {...}, "voice": {...}, "streaming": {...}, ...}
    3. Client sends text messages:
       {"type": "text", "text": "..."}
    4. Server sends:
       - {"type": "synthesis_start", "text": "...", "char_count": ...}
       - Binary audio chunks
       - {"type": "audio_complete", "text": "...", ...}
    5. Client can send control messages:
       - {"type": "flush"} - Flush buffered text
       - {"type": "reset"} - Reset buffer
       - {"type": "get_stats"} - Get statistics
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
                                if "voice" in message:
                                    session_config.voice = VoiceConfig(**message["voice"])
                                if "streaming" in message:
                                    session_config.streaming = StreamingConfig(**message["streaming"])
                                if "synthesis" in message:
                                    session_config.synthesis = SynthesisConfig(**message["synthesis"])
                                if "text_processing" in message:
                                    session_config.text_processing = TextProcessingConfig(
                                        **message["text_processing"]
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
                    
                    elif msg_type == "text":
                        # Text to synthesize
                        text_content = message.get("text", "")
                        
                        if not text_content:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Empty text provided"
                            })
                            continue
                        
                        # Create default session if not configured yet
                        if not session:
                            session = StreamingSession(websocket, session_config)
                            await session.start()
                            config_received = True
                        
                        # Process text
                        await session.process_text(text_content)
                    
                    elif msg_type in ["flush", "reset", "get_stats"]:
                        # Control messages
                        if not session:
                            # Create default session if not configured yet
                            session = StreamingSession(websocket, session_config)
                            await session.start()
                            config_received = True
                        
                        await session.handle_control_message(message)
                    
                    else:
                        logger.warning(f"Unknown message type: {msg_type}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unknown message type: {msg_type}"
                        })
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                    
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

