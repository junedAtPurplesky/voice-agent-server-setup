import os
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from faster_whisper import WhisperModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
API_KEY = os.getenv("STT_API_KEY", "stt_secret_key_production_123456")
MODEL_NAME = "large-v3-turbo"
DEVICE = "cuda"
COMPUTE_TYPE = "int8"

# Initialize FastAPI app
app = FastAPI(
    title="STT Service - Faster Whisper",
    description="Speech-to-Text Microservice with Direct API Key Authentication",
    version="1.0.0",
    root_path="/stt"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
model = None

@app.on_event("startup")
async def load_model():
    global model
    try:
        logger.info(f"Loading {MODEL_NAME} model on {DEVICE}...")
        model = WhisperModel(
            MODEL_NAME,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        logger.info("✅ STT model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise

# Validate API Key
async def validate_api_key(authorization: Optional[str] = Header(None)):
    """
    Simple Bearer token validation
    Send: Authorization: Bearer stt_secret_key_production_123456
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        if token != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

# REST Endpoint: Transcribe audio file
@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "hi",
    authorization: Optional[str] = Header(None)
):
    """
    Transcribe audio file to text
    
    Parameters:
    - file: Audio file (WAV, MP3, etc.)
    - language: Language code (hi, en, etc.)
    - authorization: Bearer {API_KEY}
    
    Example:
    curl -X POST "http://localhost/stt/transcribe?language=hi" \\
      -H "Authorization: Bearer stt_secret_key_production_123456" \\
      -F "file=@audio.wav"
    
    Response:
    {
      "success": true,
      "text": "नमस्ते, कैसे हो?",
      "language": "hi",
      "duration": 2.5,
      "segments": [...]
    }
    """
    await validate_api_key(authorization)
    
    try:
        logger.info(f"Transcribing audio: {file.filename}")
        
        # Read audio file
        audio_bytes = await file.read()
        audio_path = f"/tmp/{file.filename}"
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Transcribe with VAD
        segments, info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 200
            }
        )
        
        # Collect results
        full_text = ""
        segment_list = []
        
        for segment in segments:
            full_text += segment.text
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "confidence": segment.confidence if hasattr(segment, 'confidence') else 0.0
            })
        
        # Cleanup
        os.remove(audio_path)
        
        logger.info(f"✅ Transcription complete: {len(full_text)} characters")
        
        return {
            "success": True,
            "text": full_text,
            "language": language,
            "duration": info.duration,
            "segments": segment_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoint: Real-time transcription
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket for real-time speech-to-text streaming
    
    Connection URL:
    wss://your-domain.com/stt/ws?token=stt_secret_key_production_123456
    
    Client -> Server:
    - Send audio chunks as binary data
    
    Server -> Client (JSON):
    {
      "type": "partial",
      "text": "नमस्ते",
      "timestamp": "2025-10-28T12:00:00"
    }
    {
      "type": "final",
      "text": "नमस्ते, कैसे हो?",
      "timestamp": "2025-10-28T12:00:00"
    }
    """
    
    # Validate token
    if not token or token != API_KEY:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await websocket.accept()
    logger.info("✅ WebSocket client connected (STT)")
    
    try:
        audio_buffer = bytearray()
        
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            
            # Process when buffer reaches 32KB
            if len(audio_buffer) > 32000:
                try:
                    temp_path = "/tmp/ws_audio.wav"
                    with open(temp_path, "wb") as f:
                        f.write(bytes(audio_buffer))
                    
                    # Transcribe
                    segments, _ = model.transcribe(
                        temp_path,
                        vad_filter=True,
                        language="hi"
                    )
                    
                    text = ""
                    for segment in segments:
                        text += segment.text
                    
                    # Send partial result
                    await websocket.send_json({
                        "type": "partial",
                        "text": text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Clear buffer
                    audio_buffer.clear()
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
        logger.info("❌ WebSocket client disconnected (STT)")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "STT (Faster Whisper)",
        "model": MODEL_NAME,
        "device": DEVICE,
        "timestamp": datetime.utcnow().isoformat()
    }

# Service info
@app.get("/")
async def service_info():
    """Service information"""
    return {
        "service": "Speech-to-Text",
        "model": MODEL_NAME,
        "endpoints": {
            "transcribe": "/transcribe (POST)",
            "websocket": "/ws (WebSocket)",
            "health": "/health (GET)",
            "docs": "/docs"
        },
        "auth": "Bearer token in Authorization header"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    )
