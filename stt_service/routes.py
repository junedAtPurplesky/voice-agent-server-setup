#!/usr/bin/env python3
"""
API routes module - Speechmatics-compatible endpoints
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Path, Query, Body, Header, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import base64
import json
import time

from config import SERVICE_CONFIG, TranscriptionConfig, AudioConfig, VADConfig, SessionConfig
from transcription import TranscriptionEngine
from audio_utils import AudioConverter
from auth import get_api_key, require_auth

logger = logging.getLogger(__name__)

router = APIRouter()

# Global transcription engine reference (set by main server)
_transcription_engine: Optional[TranscriptionEngine] = None


def set_transcription_engine(engine: TranscriptionEngine):
    """Set the transcription engine instance"""
    global _transcription_engine
    _transcription_engine = engine


def get_transcription_engine() -> TranscriptionEngine:
    """Get transcription engine instance"""
    if not _transcription_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _transcription_engine


# Speechmatics-compatible request/response models
class BatchTranscriptionConfig(BaseModel):
    """Speechmatics batch transcription config"""
    language: Optional[str] = None
    output_format: str = "json"
    enable_partials: bool = False
    max_delay: float = 0.0


class BatchTranscriptionAudio(BaseModel):
    """Audio input for batch transcription"""
    content: Optional[str] = None  # Base64 encoded audio
    url: Optional[str] = None  # URL to audio file


class BatchTranscriptionRequest(BaseModel):
    """Speechmatics batch transcription request"""
    config: BatchTranscriptionConfig
    audio: BatchTranscriptionAudio


class BatchTranscriptionResponse(BaseModel):
    """Speechmatics batch transcription response"""
    id: str
    status: str
    language: Optional[str] = None
    results: Optional[list] = None


class RealtimeConfig(BaseModel):
    """Speechmatics realtime config"""
    language: Optional[str] = None
    output_format: str = "json"
    enable_partials: bool = True
    max_delay: float = 0.0


class RealtimeStartRequest(BaseModel):
    """Speechmatics realtime start request"""
    config: RealtimeConfig


@router.post("/v1/batch/transcriptions", response_model=BatchTranscriptionResponse)
@require_auth
async def create_batch_transcription(
    request: BatchTranscriptionRequest = Body(...),
    authorization: Optional[str] = Header(None)
):
    """
    Create batch transcription (Speechmatics-compatible)
    POST /v1/batch/transcriptions
    """
    engine = get_transcription_engine()
    
    try:
        # Decode audio from base64
        if not request.audio.content:
            raise HTTPException(status_code=400, detail="Audio content is required")
        
        audio_bytes = base64.b64decode(request.audio.content)
        
        # Convert audio config
        audio_config = AudioConfig()
        audio_converter = AudioConverter(audio_config)
        
        # Normalize audio
        normalized_audio = audio_converter.normalize_audio(audio_bytes)
        audio_np = audio_converter.to_numpy(normalized_audio)
        
        # Create transcription config
        trans_config = TranscriptionConfig(
            language=request.config.language,
            output_format=request.config.output_format,
            enable_partials=request.config.enable_partials,
            max_delay=request.config.max_delay
        )
        
        # Transcribe
        result = engine.transcribe(audio_np, trans_config)
        
        # Convert to Speechmatics format
        speechmatics_result = result.to_speechmatics_format(request.config.output_format)
        
        # Create response
        response = BatchTranscriptionResponse(
            id=f"batch_{int(time.time())}",
            status="completed",
            language=result.language,
            results=speechmatics_result.get("results", [])
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Batch transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/batch/transcriptions/{transcription_id}")
@require_auth
async def get_batch_transcription(
    transcription_id: str = Path(..., description="Transcription ID"),
    authorization: Optional[str] = Header(None)
):
    """
    Get batch transcription status (Speechmatics-compatible)
    GET /v1/batch/transcriptions/{transcription_id}
    """
    # For simplicity, we'll return a not found since we don't store transcriptions
    # In production, you'd want to store and retrieve transcriptions
    raise HTTPException(status_code=404, detail="Transcription not found")


@router.post("/v1/transcribe")
@require_auth
async def transcribe_file(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None),
    output_format: str = Query("json"),
    authorization: Optional[str] = Header(None)
):
    """
    Simple transcription endpoint (Speechmatics-style)
    POST /v1/transcribe
    """
    engine = get_transcription_engine()
    
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
            output_format=output_format,
            enable_partials=False
        )
        
        # Transcribe
        result = engine.transcribe(audio_np, trans_config)
        
        # Convert to Speechmatics format
        speechmatics_result = result.to_speechmatics_format(output_format)
        
        return JSONResponse(content=speechmatics_result)
        
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/config")
async def get_config(authorization: Optional[str] = Header(None)):
    """
    Get service configuration (Speechmatics-style)
    GET /v1/config
    """
    return {
        "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ko"],
        "output_formats": ["json", "text"],
        "features": {
            "partials": True,
            "realtime": True,
            "batch": True
        }
    }

