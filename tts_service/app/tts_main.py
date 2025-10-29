import os
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from scipy.io import wavfile
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
API_KEY = os.getenv("TTS_API_KEY", "tts_secret_key_production_123456")
DEVICE = "cuda"

# Initialize FastAPI app
app = FastAPI(
    title="TTS Service - CosyVoice2",
    description="Text-to-Speech Microservice with Direct API Key Authentication",
    version="1.0.0",
    root_path="/tts"
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
cosyvoice_model = None

@app.on_event("startup")
async def load_model():
    global cosyvoice_model
    try:
        logger.info("Loading CosyVoice2 model...")
        from cosyvoice.cosyvoice import CosyVoice
        
        cosyvoice_model = CosyVoice("iic/CosyVoice2-0.5B", device=DEVICE)
        logger.info("✅ TTS model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise

# Validate API Key
async def validate_api_key(authorization: Optional[str] = Header(None)):
    """Simple Bearer token validation"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        if token != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

# REST Endpoint: Synthesize text to speech
@app.post("/synthesize")
async def synthesize_speech(
    text: str,
    language: str = "hi",
    speaker: str = "default",
    authorization: Optional[str] = Header(None)
):
    """
    Convert text to speech
    
    Parameters:
    - text: Text to synthesize
    - language: Language (hi, en, etc.)
    - speaker: Speaker name (default)
    - authorization: Bearer {API_KEY}
    
    Example:
    curl -X POST "http://localhost/tts/synthesize?text=नमस्ते&language=hi" \\
      -H "Authorization: Bearer tts_secret_key_production_123456" \\
      -o output.wav
    
    Response: Audio file (WAV)
    """
    await validate_api_key(authorization)
    
    try:
        logger.info(f"Synthesizing: {text[:50]}...")
        
        # Synthesize audio
        audio_data = cosyvoice_model.inference_sft(
            text,
            speaker=speaker,
            language=language
        )
        
        # Extract audio array
        if isinstance(audio_data, dict):
            audio_array = audio_data['tts_speech']
        else:
            audio_array = audio_data
        
        # Prepare audio for output
        output_path = "/tmp/synthesis_output.wav"
        sample_rate = 22050
        
        if isinstance(audio_array, np.ndarray):
            # Normalize to [-1, 1] range
            audio_array = np.clip(audio_array, -1, 1)
            # Convert to int16
            audio_int16 = (audio_array * 32767).astype(np.int16)
            wavfile.write(output_path, sample_rate, audio_int16)
        
        # Stream file
        def file_iterator():
            with open(output_path, "rb") as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    yield chunk
        
        logger.info("✅ Audio synthesis complete")
        
        return StreamingResponse(
            file_iterator(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=output.wav"}
        )
    
    except Exception as e:
        logger.error(f"❌ Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoint: Real-time synthesis
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket for real-time text-to-speech streaming
    
    Connection URL:
    wss://your-domain.com/tts/ws?token=tts_secret_key_production_123456
    
    Client -> Server (JSON):
    {
      "text": "नमस्ते, आप कैसे हैं?",
      "language": "hi",
      "speaker": "default"
    }
    
    Server -> Client:
    - Binary audio chunks
    - JSON with type="complete"
    """
    
    # Validate token
    if not token or token != API_KEY:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await websocket.accept()
    logger.info("✅ WebSocket client connected (TTS)")
    
    try:
        while True:
            # Receive text from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            text = message.get("text", "")
            language = message.get("language", "hi")
            speaker = message.get("speaker", "default")
            
            try:
                # Synthesize audio
                audio_data = cosyvoice_model.inference_sft(
                    text,
                    speaker=speaker,
                    language=language
                )
                
                # Extract audio array
                if isinstance(audio_data, dict):
                    audio_array = audio_data['tts_speech']
                else:
                    audio_array = audio_data
                
                # Convert to bytes
                if isinstance(audio_array, np.ndarray):
                    audio_array = np.clip(audio_array, -1, 1)
                    audio_bytes = (audio_array * 32767).astype(np.int16).tobytes()
                    
                    # Send audio chunks
                    chunk_size = 4096
                    for i in range(0, len(audio_bytes), chunk_size):
                        chunk = audio_bytes[i:i+chunk_size]
                        await websocket.send_bytes(chunk)
                    
                    # Signal completion
                    await websocket.send_json({
                        "type": "complete",
                        "duration": len(audio_bytes) / (2 * 22050),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
        logger.info("❌ WebSocket client disconnected (TTS)")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TTS (CosyVoice2)",
        "model": "CosyVoice2-0.5B",
        "device": DEVICE,
        "timestamp": datetime.utcnow().isoformat()
    }

# Service info
@app.get("/")
async def service_info():
    """Service information"""
    return {
        "service": "Text-to-Speech",
        "model": "CosyVoice2-0.5B",
        "endpoints": {
            "synthesize": "/synthesize (POST)",
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
        port=8001,
        workers=1,
        log_level="info"
    )
