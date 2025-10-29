"""HTTP endpoints for STT service"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, Request
from .config import config_manager, TranscriptionConfig
from .models import stt_processor
from .auth import auth_manager, request_validator
from .utils import response_formatter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio_file(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    authorization: Optional[str] = Header(None)
):
    """Transcribe audio file to text"""
    start_time = datetime.utcnow()
    
    try:
        auth_manager.validate_api_key(authorization)
        
        # Save uploaded file
        temp_file = f"/tmp/{file.filename}"
        content = await file.read()
        with open(temp_file, "wb") as f:
            f.write(content)
        
        # Create config
        config = TranscriptionConfig(
            language=request_validator.validate_language(language),
            vad_config=config_manager.get_config().transcription.vad_config
        )
        
        # Process transcription
        result = await stt_processor.process_file(temp_file, config)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return response_formatter.format_transcription_response(result, config, processing_time)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configuration(request: Request, authorization: Optional[str] = Header(None)):
    """Get current configuration"""
    try:
        auth_manager.validate_api_key(authorization)
        config = config_manager.get_config()
        
        return {
            "success": True,
            "config": {
                "model": config.model.dict(),
                "transcription": config.transcription.dict()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "STT Service",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/")
async def service_info():
    """Service information"""
    return {
        "service": "Speech-to-Text Service",
        "version": "2.0.0",
        "endpoints": {
            "transcribe": "/transcribe (POST)",
            "websocket_realtime": "/ws/realtime (WebSocket)",
            "websocket_fullduplex": "/ws/fullduplex (WebSocket)",
            "config": "/config (GET)",
            "health": "/health (GET)"
        }
    }

