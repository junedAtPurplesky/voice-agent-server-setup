#!/usr/bin/env python3
"""
ElevenLabs-compatible TTS Service
High-performance text-to-speech service with full ElevenLabs API compatibility
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, Tuple

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Path, Query, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
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
from auth import auth_manager, initialize_auth
from elevenlabs_models import (
    TextToSpeechRequest,
    VoiceSettings,
    Voice,
    VoicesResponse,
    Model,
    ModelsResponse
)
from model_mapper import ModelMapper, AVAILABLE_MODELS

# Routes will be imported after synthesis_engine is initialized

# Configure logging
logging.basicConfig(
    level=getattr(logging, SERVICE_CONFIG.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ElevenLabs-Compatible TTS Service",
    version="1.0.0",
    description="ElevenLabs-compatible text-to-speech service API"
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


# Voice settings conversion moved to routes module


class StreamingSession:
    """Manages a streaming TTS session (ElevenLabs-compatible)"""
    
    def __init__(
        self,
        websocket: WebSocket,
        voice_id: str,
        model_id: str,
        voice_settings: Optional[VoiceSettings] = None
    ):
        self.websocket = websocket
        self.voice_id = voice_id
        self.model_id = model_id
        self.voice_settings = voice_settings or VoiceSettings()
        
        # Convert to internal configs
        from routes import convert_voice_settings_to_config
        voice_config, synthesis_config = convert_voice_settings_to_config(self.voice_settings)
        voice_config.speaker = voice_id  # Use voice_id as speaker
        
        # Create session config
        session_config = SessionConfig()
        session_config.voice = voice_config
        session_config.synthesis = synthesis_config
        session_config.audio = AudioConfig(encoding="pcm_s16le", sample_rate=24000)
        
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
        
        logger.info(f"Streaming session created: voice_id={voice_id}, model_id={model_id}")
    
    async def start(self):
        """Start the session"""
        await self.websocket.send_json({
            "type": "session_started",
            "message": "Streaming session ready"
        })
    
    async def stop(self):
        """Stop the session"""
        self.is_active = False
        if self.text_buffer.has_data():
            await self._process_buffered_text()
    
    async def process_text(self, text: str):
        """Process incoming text chunk"""
        try:
            if len(text) > SERVICE_CONFIG.max_text_length:
                await self.send_error(f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)")
                return
            
            ready_sentences = self.text_buffer.add_text(text)
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
        """Synthesize a batch of sentences"""
        try:
            text = " ".join(sentences)
            self.total_chars_processed += len(text)
            
            from routes import convert_voice_settings_to_config
            voice_config, synthesis_config = convert_voice_settings_to_config(self.voice_settings)
            voice_config.speaker = self.voice_id
            
            if synthesis_engine:
                chunk_count = 0
                start_time = time.time()
                
                for audio_chunk in synthesis_engine.synthesize_streaming(
                    text,
                    voice_config,
                    synthesis_config,
                    chunk_size=1024
                ):
                    audio_bytes = self.audio_converter.convert_audio(
                        audio_chunk,
                        24000
                    )
                    await self.websocket.send_bytes(audio_bytes)
                    chunk_count += 1
                
                processing_time = time.time() - start_time
                await self.websocket.send_json({
                    "type": "audio_complete",
                    "text": text,
                    "chunks_sent": chunk_count,
                    "processing_time": processing_time
                })
                
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            await self.send_error(f"Synthesis failed: {e}")
    
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
    logger.info("ElevenLabs-Compatible TTS Service v1.0.0")
    logger.info("=" * 60)
    
    try:
        global synthesis_engine
        
        # Initialize authentication first
        initialize_auth(
            require_auth=SERVICE_CONFIG.require_auth,
            api_keys=SERVICE_CONFIG.api_keys if SERVICE_CONFIG.api_keys else None
        )
        
        # Initialize synthesis engine
        synthesis_engine = SynthesisEngine(SERVICE_CONFIG)
        
        # Import and setup routes after engine is initialized
        from routes import router as api_router, set_synthesis_engine
        set_synthesis_engine(synthesis_engine)
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
    model_info = synthesis_engine.get_model_info() if synthesis_engine else {}
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "ElevenLabs-Compatible TTS",
        **model_info
    }


# ElevenLabs-compatible routes will be included after startup


@app.websocket("/v1/text-to-speech/{voice_id}/stream")
async def websocket_text_to_speech_stream(
    websocket: WebSocket,
    voice_id: str = Path(..., description="Voice ID"),
    model_id: Optional[str] = Query(None, description="Model ID"),
    xi_api_key: Optional[str] = Query(None, description="API key")
):
    """
    WebSocket streaming TTS (ElevenLabs-compatible)
    
    Protocol:
    1. Client connects
    2. Client sends text messages: {"text": "..."}
    3. Server streams audio chunks
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established: voice_id={voice_id}")
    
    # Parse voice settings from query or use defaults
    voice_settings = VoiceSettings()
    model_id = model_id or ModelMapper.get_default_model()
    
    session: Optional[StreamingSession] = None
    
    try:
        session = StreamingSession(websocket, voice_id, model_id, voice_settings)
        await session.start()
        
        while True:
            data = await websocket.receive()
            
            if "text" in data:
                try:
                    message = json.loads(data["text"])
                    msg_type = message.get("type")
                    
                    if msg_type == "text" or "text" in message:
                        text_content = message.get("text", "")
                        if text_content:
                            await session.process_text(text_content)
                    
                    elif msg_type == "flush":
                        await session.flush()
                    
                    elif msg_type == "reset":
                        session.text_buffer.reset()
                        await websocket.send_json({
                            "type": "status",
                            "message": "Buffer reset"
                        })
                    
                    else:
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


# Legacy endpoints (for backward compatibility)
@app.get("/voices")
async def list_voices_legacy():
    """Legacy voices endpoint"""
    return await list_voices()


@app.post("/synthesize")
async def synthesize_legacy(request: Dict[str, Any]):
    """Legacy synthesis endpoint"""
    # Convert legacy format to new format
    voice_id = request.get("voice_config", {}).get("speaker", "default")
    text = request.get("text", "")
    
    tts_request = TextToSpeechRequest(
        text=text,
        voice_settings=VoiceSettings()
    )
    
    return await text_to_speech(voice_id=voice_id, request=tts_request)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=SERVICE_CONFIG.host,
        port=SERVICE_CONFIG.port,
        log_level=SERVICE_CONFIG.log_level,
        access_log=True
    )
