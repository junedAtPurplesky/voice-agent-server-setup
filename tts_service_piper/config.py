#!/usr/bin/env python3
"""
Configuration models for Piper TTS service
Production-ready with multi-language support (Hindi & English)
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field
import os


class ServiceConfig(BaseModel):
    """Server-level configuration"""
    models_dir: str = "piper_models"  # Directory for Piper models
    host: str = "0.0.0.0"
    port: int = 8003  # Different port to avoid conflict with CosyVoice
    log_level: str = "info"
    max_text_length: int = 5000
    
    # GPU Configuration
    use_gpu: bool = False  # Enable GPU acceleration (requires onnxruntime-gpu and CUDA)
    gpu_device_id: int = 0  # GPU device ID to use
    
    # Default voices for different languages
    default_hindi_voice: str = "hi_IN-madhur-medium"
    default_english_voice: str = "en_US-lessac-medium"


class AudioConfig(BaseModel):
    """Audio output configuration - client configurable"""
    sample_rate: int = Field(default=22050, description="Output audio sample rate in Hz (Piper default: 22050)")
    channels: int = Field(default=1, description="Number of audio channels (1=mono, 2=stereo)")
    encoding: Literal["pcm_s16le", "pcm_f32le", "mp3", "opus", "wav"] = Field(
        default="pcm_s16le",
        description="Audio encoding format"
    )
    bitrate: Optional[int] = Field(
        default=128,
        description="Bitrate for lossy formats (kbps)"
    )
    
    @property
    def bytes_per_sample(self) -> int:
        """Get bytes per sample based on encoding"""
        if self.encoding == "pcm_s16le":
            return 2
        elif self.encoding == "pcm_f32le":
            return 4
        return 2  # Default


class VoiceConfig(BaseModel):
    """Voice and style configuration for Piper"""
    voice_model: str = Field(
        default="en_US-lessac-medium",
        description="Piper voice model to use. Available models: Hindi (hi_IN-*), English (en_US-*, en_GB-*)"
    )
    language: Literal["en", "hi"] = Field(
        default="en",
        description="Language code (en=English, hi=Hindi)"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech rate multiplier (0.5=slow, 1.0=normal, 2.0=fast)"
    )
    volume: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Volume multiplier"
    )


class StreamingConfig(BaseModel):
    """Streaming configuration for low-latency output"""
    enabled: bool = Field(
        default=True,
        description="Enable streaming mode"
    )
    chunk_size: int = Field(
        default=1024,
        ge=256,
        le=4096,
        description="Audio chunk size in samples for streaming"
    )
    flush_threshold: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of text sentences to accumulate before flushing audio"
    )
    optimize_streaming_latency: int = Field(
        default=2,
        ge=0,
        le=4,
        description="Latency optimization level (0=quality, 4=fastest)"
    )
    enable_ssml_parsing: bool = Field(
        default=False,
        description="Enable SSML (Speech Synthesis Markup Language) parsing"
    )
    buffer_size: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of audio chunks to buffer before streaming starts"
    )
    sentence_silence_duration: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Silence duration between sentences in seconds"
    )


class SynthesisConfig(BaseModel):
    """Text-to-speech synthesis configuration for Piper"""
    noise_scale: float = Field(
        default=0.667,
        ge=0.0,
        le=1.0,
        description="Noise scale for synthesis (affects variability)"
    )
    length_scale: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Length scale (affects speed, similar to speed parameter)"
    )
    noise_w: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Noise weight for synthesis"
    )


class TextProcessingConfig(BaseModel):
    """Text preprocessing configuration"""
    normalize_text: bool = Field(
        default=True,
        description="Enable text normalization (numbers, abbreviations, etc.)"
    )
    split_sentences: bool = Field(
        default=True,
        description="Automatically split text into sentences for better streaming"
    )
    remove_special_chars: bool = Field(
        default=False,
        description="Remove special characters from text"
    )
    max_sentence_length: int = Field(
        default=500,
        ge=50,
        le=2000,
        description="Maximum length of a single sentence in characters"
    )


class SessionConfig(BaseModel):
    """Complete session configuration combining all configs"""
    audio: AudioConfig = Field(default_factory=AudioConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    synthesis: SynthesisConfig = Field(default_factory=SynthesisConfig)
    text_processing: TextProcessingConfig = Field(default_factory=TextProcessingConfig)
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio": {
                    "sample_rate": 22050,
                    "channels": 1,
                    "encoding": "pcm_s16le"
                },
                "voice": {
                    "voice_model": "en_US-lessac-medium",
                    "language": "en",
                    "speed": 1.0
                },
                "streaming": {
                    "enabled": True,
                    "chunk_size": 1024,
                    "flush_threshold": 3,
                    "optimize_streaming_latency": 2
                },
                "synthesis": {
                    "noise_scale": 0.667,
                    "length_scale": 1.0,
                    "noise_w": 0.8
                },
                "text_processing": {
                    "normalize_text": True,
                    "split_sentences": True
                }
            }
        }


# Available Piper voices
PIPER_VOICES = {
    "en": [
        {"id": "en_US-lessac-medium", "name": "Lessac (US, Medium Quality)", "gender": "male"},
        {"id": "en_US-libritts-high", "name": "LibriTTS (US, High Quality)", "gender": "neutral"},
        {"id": "en_US-amy-medium", "name": "Amy (US, Medium Quality)", "gender": "female"},
        {"id": "en_US-danny-low", "name": "Danny (US, Low Quality)", "gender": "male"},
        {"id": "en_GB-alan-medium", "name": "Alan (GB, Medium Quality)", "gender": "male"},
        {"id": "en_GB-northern_english_male-medium", "name": "Northern English (GB, Medium Quality)", "gender": "male"},
    ],
    "hi": [
        {"id": "hi_IN-madhur-medium", "name": "Madhur (India, Medium Quality)", "gender": "male"},
        {"id": "hi_IN-female-medium", "name": "Female (India, Medium Quality)", "gender": "female"},
    ]
}


# Default service configuration
SERVICE_CONFIG = ServiceConfig()

