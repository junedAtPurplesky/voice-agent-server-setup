#!/usr/bin/env python3
"""
API routes module - ElevenLabs-compatible endpoints with complete format support
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query, Body, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
import logging
import json
import base64
import asyncio

from config import SERVICE_CONFIG, VoiceConfig, SynthesisConfig
from synthesis import SynthesisEngine
from audio_utils import AudioConverter
from elevenlabs_models import (
    TextToSpeechRequest,
    VoiceSettings,
    Voice,
    VoicesResponse,
    Model,
    ModelsResponse
)
from elevenlabs_formats import validate_output_format, DEFAULT_OUTPUT_FORMAT
from model_mapper import ModelMapper, AVAILABLE_MODELS
from auth import auth_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Global synthesis engine reference
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
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    
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
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    models = [Model(**model_data) for model_data in AVAILABLE_MODELS]
    return ModelsResponse(models=models)


@router.post("/v1/text-to-speech/{voice_id}")
async def text_to_speech(
    voice_id: str = Path(..., description="Voice ID"),
    request: TextToSpeechRequest = Body(...),
    xi_api_key: Optional[str] = Header(None, alias="xi-api-key"),
    output_format: Optional[str] = Query(None, description="Output format (can also be in request body)"),
    optimize_streaming_latency: Optional[int] = Query(0, ge=0, le=4)
):
    """Convert text to speech (ElevenLabs-compatible)"""
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    engine = get_synthesis_engine()
    
    if len(request.text) > SERVICE_CONFIG.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)"
        )
    
    # Support output_format from request body (ElevenLabs-style) or query parameter
    format_to_use = request.output_format or output_format or DEFAULT_OUTPUT_FORMAT
    
    # Validate format
    if not validate_output_format(format_to_use):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: {format_to_use}. Use /v1/models endpoint to see supported formats."
        )
    
    voice_config, synthesis_config = convert_voice_settings_to_config(
        request.voice_settings or VoiceSettings()
    )
    voice_config.speaker = voice_id
    
    try:
        result = engine.synthesize(request.text, voice_config, synthesis_config)
        audio_converter = AudioConverter(format_to_use)
        audio_bytes = audio_converter.convert_audio(result.audio, result.sample_rate)
        
        codec = format_to_use.split("_")[0]
        media_type_map = {
            "mp3": "audio/mpeg",
            "pcm": "audio/pcm",
            "wav": "audio/wav",
            "opus": "audio/opus",
            "ulaw": "audio/basic",
            "alaw": "audio/basic"
        }
        media_type = media_type_map.get(codec, "audio/wav")
        
        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename=\"audio.{codec}\"',
                "Content-Length": str(len(audio_bytes))
            }
        )
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/text-to-speech/{voice_id}/stream")
async def text_to_speech_stream(
    voice_id: str = Path(..., description="Voice ID"),
    request: TextToSpeechRequest = Body(...),
    xi_api_key: Optional[str] = Header(None, alias="xi-api-key"),
    output_format: Optional[str] = Query(None, description="Output format (can also be in request body)"),
    optimize_streaming_latency: Optional[int] = Query(0, ge=0, le=4)
):
    """Stream text to speech (ElevenLabs-compatible)"""
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    engine = get_synthesis_engine()
    
    if len(request.text) > SERVICE_CONFIG.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)"
        )
    
    # Support output_format from request body (ElevenLabs-style) or query parameter
    format_to_use = request.output_format or output_format or DEFAULT_OUTPUT_FORMAT
    
    # Validate format
    if not validate_output_format(format_to_use):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: {format_to_use}. Use /v1/models endpoint to see supported formats."
        )
    
    voice_config, synthesis_config = convert_voice_settings_to_config(
        request.voice_settings or VoiceSettings()
    )
    voice_config.speaker = voice_id
    
    audio_converter = AudioConverter(format_to_use)
    
    async def generate_audio():
        try:
            result = engine.synthesize(request.text, voice_config, synthesis_config)
            chunks = audio_converter.chunk_for_streaming(result.audio, result.sample_rate)
            
            for chunk in chunks:
                yield chunk
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            raise
    
    codec = format_to_use.split("_")[0]
    media_type_map = {
        "mp3": "audio/mpeg",
        "pcm": "audio/pcm",
        "wav": "audio/wav",
        "opus": "audio/opus",
        "ulaw": "audio/basic",
        "alaw": "audio/basic"
    }
    media_type = media_type_map.get(codec, "audio/wav")
    
    return StreamingResponse(
        generate_audio(),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename=\"audio.{codec}\"',
            "Cache-Control": "no-cache"
        }
    )


@router.websocket("/v1/text-to-speech/{voice_id}/stream-input")
async def websocket_tts_stream_input(
    websocket: WebSocket,
    voice_id: str,
    model_id: str = Query("eleven_multilingual_v2"),
    optimize_streaming_latency: int = Query(0, ge=0, le=4),
    output_format: str = Query("mp3_44100_128"),
    enable_ssml_parsing: bool = Query(False)
):
    """WebSocket endpoint - ElevenLabs-compatible streaming"""
    await websocket.accept()
    
    xi_api_key = websocket.headers.get("xi-api-key")
    
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            await websocket.close(code=4403)
            logger.warning("WebSocket: Invalid API key")
            return
    
    engine = get_synthesis_engine()
    
    # WebSocket format can be updated via messages, start with query param default
    current_format = output_format
    audio_converter = AudioConverter(current_format)
    
    text_buffer = ""
    voice_settings = VoiceSettings()
    
    try:
        logger.info(f"WebSocket connected: voice={voice_id}, format={current_format}")
        
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            
            if "xi_api_key" in data:
                xi_api_key = data["xi_api_key"]
                if auth_manager and auth_manager.require_auth:
                    if not auth_manager.validate_api_key(xi_api_key):
                        await websocket.send_json({"error": "Invalid API key"})
                        await websocket.close(code=4403)
                        return
            
            if "voice_settings" in data:
                voice_settings = VoiceSettings(**data["voice_settings"])
            
            # Support output_format in WebSocket messages (ElevenLabs-style)
            if "output_format" in data:
                new_format = data["output_format"]
                if validate_output_format(new_format):
                    current_format = new_format
                    audio_converter = AudioConverter(current_format)
                    logger.info(f"WebSocket: Updated output format to {current_format}")
                else:
                    await websocket.send_json({"error": f"Invalid output format: {new_format}"})
                    logger.warning(f"WebSocket: Invalid format requested: {new_format}")
            
            text = data.get("text", "")
            flush = data.get("flush", False)
            try_trigger = data.get("try_trigger_generation", False)
            close_conn = data.get("close", False)
            
            if close_conn:
                logger.info("WebSocket: explicit close requested by client")
                await websocket.close()
                return
            
            # Empty text just flushes, doesn't close
            if text == "":
                if text_buffer.strip():
                    await generate_and_send_audio(
                        engine, websocket, text_buffer, voice_id,
                        voice_settings, audio_converter, is_final=True
                    )
                    text_buffer = ""
                await websocket.send_json({"event": "ready"})
                continue
            
            if text.strip():
                text_buffer += text
            
            should_generate = flush or (
                try_trigger and len(text_buffer) >= 50
            ) or len(text_buffer) >= 200
            
            if should_generate and text_buffer.strip():
                await generate_and_send_audio(
                    engine, websocket, text_buffer, voice_id,
                    voice_settings, audio_converter, is_final=False
                )
                text_buffer = ""
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
        await websocket.close()


async def generate_and_send_audio(
    engine: SynthesisEngine,
    websocket: WebSocket,
    text: str,
    voice_id: str,
    voice_settings: VoiceSettings,
    audio_converter: AudioConverter,
    is_final: bool = False
):
    """Generate audio and send in ElevenLabs WebSocket format"""
    try:
        voice_config, synthesis_config = convert_voice_settings_to_config(voice_settings)
        voice_config.speaker = voice_id
        
        result = engine.synthesize(text, voice_config, synthesis_config)
        chunks = audio_converter.chunk_for_streaming(result.audio, result.sample_rate)
        
        logger.info(f"WebSocket: Sending {len(chunks)} audio chunks for text: '{text[:50]}...'")
        
        for i, chunk in enumerate(chunks):
            b64_audio = base64.b64encode(chunk).decode("utf-8")
            
            response = {
                "audio": b64_audio,
                "isFinal": is_final and (i == len(chunks) - 1)
            }
            
            if i == 0:
                response["normalizedAlignment"] = {
                    "chars": list(text),
                    "charStartTimesMs": [i * 50 for i in range(len(text))],
                    "charDurationsMs": [50] * len(text)
                }
            
            await websocket.send_json(response)
            await asyncio.sleep(0.01)
            
    except Exception as e:
        logger.error(f"Audio generation error: {e}", exc_info=True)
        await websocket.send_json({"error": str(e)})