#!/usr/bin/env python3
"""
API routes module - ElevenLabs-compatible endpoints
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query, Body, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
import logging
import json
import base64

from config import SERVICE_CONFIG, VoiceConfig, SynthesisConfig
from synthesis import SynthesisEngine
from audio_utils import AudioConverter
from config import AudioConfig
from elevenlabs_models import (
    TextToSpeechRequest,
    VoiceSettings,
    Voice,
    VoicesResponse,
    Model,
    ModelsResponse
)
from model_mapper import ModelMapper, AVAILABLE_MODELS
from auth import auth_manager  # ✅ Added to handle xi-api-key authentication

logger = logging.getLogger(__name__)

router = APIRouter()

# Global synthesis engine reference (set by main server)
_synthesis_engine: Optional[SynthesisEngine] = None


def set_synthesis_engine(engine: SynthesisEngine):
    """Set the synthesis engine instance"""
    global _synthesis_engine
    _synthesis_engine = engine


def get_synthesis_engine() -> SynthesisEngine:
    """Get synthesis engine instance"""
    if not _synthesis_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _synthesis_engine


def convert_voice_settings_to_config(voice_settings: VoiceSettings) -> tuple[VoiceConfig, SynthesisConfig]:
    """Convert ElevenLabs voice settings to internal configs"""
    voice_config = VoiceConfig(
        speed=1.0,
        pitch=1.0,
        energy=voice_settings.stability
    )
    
    synthesis_config = SynthesisConfig(
        stability=voice_settings.stability,
        similarity_boost=voice_settings.similarity_boost,
        use_speaker_boost=voice_settings.use_speaker_boost,
        temperature=0.7
    )
    
    return voice_config, synthesis_config


@router.get("/v1/voices", response_model=VoicesResponse)
async def list_voices(xi_api_key: Optional[str] = Header(None, alias="xi-api-key")):
    """List available voices (ElevenLabs-compatible)"""
    engine = get_synthesis_engine()
    voices_list = engine.list_voices()
    
    voices = []
    for voice_data in voices_list:
        voice = Voice(
            voice_id=voice_data["id"],
            name=voice_data["name"],
            category="premade",
            labels={"language": voice_data.get("language", "multi")},
            description=f"Voice: {voice_data['name']}"
        )
        voices.append(voice)
    
    return VoicesResponse(voices=voices)


@router.get("/v1/models", response_model=ModelsResponse)
async def list_models(xi_api_key: Optional[str] = Header(None, alias="xi-api-key")):
    """List available models (ElevenLabs-compatible)"""
    models = [Model(**model_data) for model_data in AVAILABLE_MODELS]
    return ModelsResponse(models=models)


@router.post("/v1/text-to-speech/{voice_id}")
async def text_to_speech(
    voice_id: str = Path(..., description="Voice ID"),
    request: TextToSpeechRequest = Body(...),
    xi_api_key: Optional[str] = Header(None, alias="xi-api-key"),
    output_format: Optional[str] = Query("mp3_44100_128", description="Output format"),
    optimize_streaming_latency: Optional[int] = Query(0, ge=0, le=4, description="Streaming latency optimization")
):
    """Convert text to speech (ElevenLabs-compatible)"""
    engine = get_synthesis_engine()
    
    if len(request.text) > SERVICE_CONFIG.max_text_length:
        raise HTTPException(status_code=400, detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)")
    
    cosyvoice_model = ModelMapper.elevenlabs_to_cosyvoice(
        request.model_id or ModelMapper.get_default_model()
    )
    
    voice_config, synthesis_config = convert_voice_settings_to_config(request.voice_settings or VoiceSettings())
    voice_config.speaker = voice_id
    
    try:
        result = engine.synthesize(request.text, voice_config, synthesis_config)
        format_parts = output_format.split("_")
        encoding = format_parts[0]
        sample_rate = int(format_parts[1]) if len(format_parts) > 1 else 24000
        
        audio_config = AudioConfig(
            encoding="wav" if encoding == "mp3" else "pcm_s16le",
            sample_rate=sample_rate
        )
        audio_converter = AudioConverter(audio_config)
        audio_bytes = audio_converter.convert_audio(result.audio, result.sample_rate)
        
        media_type = "audio/wav" if encoding == "mp3" else "audio/pcm"
        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="tts_output.{encoding if encoding != "mp3" else "wav"}"'}
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/text-to-speech/{voice_id}/stream")
async def text_to_speech_stream(
    voice_id: str = Path(..., description="Voice ID"),
    request: TextToSpeechRequest = Body(...),
    xi_api_key: Optional[str] = Header(None, alias="xi-api-key"),
    output_format: Optional[str] = Query("pcm_24000", description="Output format")
):
    """Stream text to speech (ElevenLabs-compatible)"""
    engine = get_synthesis_engine()
    
    if len(request.text) > SERVICE_CONFIG.max_text_length:
        raise HTTPException(status_code=400, detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)")
    
    voice_config, synthesis_config = convert_voice_settings_to_config(request.voice_settings or VoiceSettings())
    voice_config.speaker = voice_id
    
    audio_config = AudioConfig(encoding="pcm_s16le", sample_rate=24000)
    audio_converter = AudioConverter(audio_config)
    
    async def generate_audio():
        try:
            for audio_chunk in engine.synthesize_streaming(request.text, voice_config, synthesis_config, chunk_size=1024):
                audio_bytes = audio_converter.convert_audio(audio_chunk, 24000)
                yield audio_bytes
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
    
    return StreamingResponse(generate_audio(), media_type="audio/pcm")


# ---------------------------------------------------------------------
# 🧠 NEW: ElevenLabs-Compatible WebSocket Endpoint (same behavior)
# ---------------------------------------------------------------------
@router.websocket("/v1/text-to-speech/{voice_id}/stream-input")
async def websocket_tts_stream_input(
    websocket: WebSocket,
    voice_id: str,
    model_id: str = Query("eleven_multilingual_v2"),
    optimize_streaming_latency: int = Query(1, ge=0, le=4),
    output_format: str = Query("pcm_16000"),
):
    """
    WebSocket endpoint compatible with ElevenLabs /v1/text-to-speech/{voice_id}/stream-input
    Allows sending text chunks and receiving audio in real time.
    """
    await websocket.accept()

    # 🔒 API key validation (same as other routes)
    xi_api_key = websocket.headers.get("xi-api-key")
    if auth_manager.require_auth and not auth_manager.validate_api_key(xi_api_key):
        await websocket.close(code=4403)  # Forbidden
        logger.warning("403 WebSocket connection rejected: invalid API key")
        return

    engine = get_synthesis_engine()
    audio_config = AudioConfig(encoding="pcm_s16le", sample_rate=16000)
    audio_converter = AudioConverter(audio_config)

    text_buffer = ""
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            text = data.get("text", "")
            flush = data.get("flush", False)

            if text.strip():
                text_buffer += text.strip() + " "

            if flush and text_buffer.strip():
                voice_config, synthesis_config = convert_voice_settings_to_config(VoiceSettings())
                voice_config.speaker = voice_id
                for chunk in engine.synthesize_streaming(text_buffer, voice_config, synthesis_config, chunk_size=1024):
                    audio_bytes = audio_converter.convert_audio(chunk, 16000)
                    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    await websocket.send_json({"audio": b64_audio})
                await websocket.send_json({"isFinal": True})
                text_buffer = ""

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected cleanly")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
        await websocket.close()
