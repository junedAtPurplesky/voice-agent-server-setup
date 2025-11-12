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
    # Validate API key if auth is required
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
    # Validate API key if auth is required
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
    output_format: Optional[str] = Query("mp3_44100_128", description="Output format"),
    optimize_streaming_latency: Optional[int] = Query(0, ge=0, le=4)
):
    """
    Convert text to speech (ElevenLabs-compatible)
    
    Supported formats:
    - mp3_44100_128 (default)
    - mp3_44100_64, mp3_44100_96, mp3_44100_192
    - mp3_22050_32, mp3_44100_32
    - pcm_16000, pcm_22050, pcm_24000, pcm_44100
    - ulaw_8000 (Twilio compatible)
    - alaw_8000
    """
    # Validate API key if auth is required
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    engine = get_synthesis_engine()
    
    if len(request.text) > SERVICE_CONFIG.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)"
        )
    
    voice_config, synthesis_config = convert_voice_settings_to_config(
        request.voice_settings or VoiceSettings()
    )
    voice_config.speaker = voice_id
    
    try:
        # Synthesize complete audio
        result = engine.synthesize(request.text, voice_config, synthesis_config)
        
        # Convert to target format using FFmpeg-enabled converter
        audio_converter = AudioConverter(output_format)
        audio_bytes = audio_converter.convert_audio(result.audio, result.sample_rate)
        
        # Determine media type based on codec
        codec = output_format.split("_")[0]
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
                "Content-Disposition": f'attachment; filename="audio.{codec}"',
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
    output_format: Optional[str] = Query("mp3_44100_128", description="Output format"),
    optimize_streaming_latency: Optional[int] = Query(0, ge=0, le=4)
):
    """
    Stream text to speech (ElevenLabs-compatible)
    
    Returns audio in chunks with specified format.
    Chunks are sized appropriately for smooth streaming (8192 samples for PCM).
    """
    # Validate API key if auth is required
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    engine = get_synthesis_engine()
    
    if len(request.text) > SERVICE_CONFIG.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long (max {SERVICE_CONFIG.max_text_length} chars)"
        )
    
    voice_config, synthesis_config = convert_voice_settings_to_config(
        request.voice_settings or VoiceSettings()
    )
    voice_config.speaker = voice_id
    
    audio_converter = AudioConverter(output_format)
    
    async def generate_audio():
        try:
            # Generate full audio
            result = engine.synthesize(request.text, voice_config, synthesis_config)
            
            # Split into proper streaming chunks (ElevenLabs-style)
            chunks = audio_converter.chunk_for_streaming(result.audio, result.sample_rate)
            
            logger.info(f"Streaming {len(chunks)} chunks for text length {len(request.text)}")
            
            for i, chunk in enumerate(chunks):
                yield chunk
                # Small delay for network smoothness
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            raise
    
    codec = output_format.split("_")[0]
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
            "Content-Disposition": f'attachment; filename="audio.{codec}"',
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
    """
    WebSocket endpoint - ElevenLabs /v1/text-to-speech/{voice_id}/stream-input
    
    Protocol:
    1. Client connects
    2. Client sends: {"text": "...", "voice_settings": {...}, "xi_api_key": "..."}
    3. Client sends text: {"text": "chunk ", "try_trigger_generation": false}
    4. Client flushes: {"text": "final chunk", "flush": true}
    5. Client closes: {"text": ""}
    6. Server responds: {"audio": "base64...", "isFinal": false/true}
    
    Default format: mp3_44100_128
    Supported: All ElevenLabs formats
    """
    await websocket.accept()
    
    # Get API key from header
    xi_api_key = websocket.headers.get("xi-api-key")
    
    # Validate API key if auth is required
    if auth_manager and auth_manager.require_auth:
        if not auth_manager.validate_api_key(xi_api_key):
            await websocket.close(code=4403)  # Forbidden
            logger.warning("WebSocket: Invalid API key")
            return
    
    engine = get_synthesis_engine()
    audio_converter = AudioConverter(output_format)
    
    text_buffer = ""
    voice_settings = VoiceSettings()
    
    try:
        logger.info(f"WebSocket connected: voice={voice_id}, format={output_format}")
        
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            
            # Handle API key from first message
            if "xi_api_key" in data:
                xi_api_key = data["xi_api_key"]
                if auth_manager and auth_manager.require_auth:
                    if not auth_manager.validate_api_key(xi_api_key):
                        await websocket.send_json({"error": "Invalid API key"})
                        await websocket.close(code=4403)
                        return
            
            # Handle voice settings update
            if "voice_settings" in data:
                voice_settings = VoiceSettings(**data["voice_settings"])
            
            # Get text
            text = data.get("text", "")
            flush = data.get("flush", False)
            try_trigger = data.get("try_trigger_generation", False)
            
            # EOS: empty string closes connection
            if text == "":
                if text_buffer.strip():
                    # Generate final audio
                    await generate_and_send_audio(
                        engine, websocket, text_buffer, voice_id,
                        voice_settings, audio_converter, is_final=True
                    )
                logger.info("WebSocket: EOS received, closing")
                break
            
            # Add text to buffer
            if text.strip():
                text_buffer += text
            
            # Determine if we should generate
            should_generate = False
            
            if flush:
                should_generate = True
            elif try_trigger and len(text_buffer) >= 50:
                should_generate = True
            elif len(text_buffer) >= 200:  # Auto-trigger at 200 chars
                should_generate = True
            
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
        
        # Generate audio
        result = engine.synthesize(text, voice_config, synthesis_config)
        
        # Convert and chunk audio (using FFmpeg-enabled converter)
        chunks = audio_converter.chunk_for_streaming(result.audio, result.sample_rate)
        
        logger.info(f"WebSocket: Sending {len(chunks)} audio chunks for text: '{text[:50]}...'")
        
        # Send each chunk in ElevenLabs format
        for i, chunk in enumerate(chunks):
            b64_audio = base64.b64encode(chunk).decode("utf-8")
            
            response = {
                "audio": b64_audio,
                "isFinal": is_final and (i == len(chunks) - 1)
            }
            
            # Add alignment info on first chunk
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