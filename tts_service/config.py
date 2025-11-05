#!/usr/bin/env python3
"""
Configuration models for TTS service
Production-ready with ElevenLabs-style streaming configurations
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field
import torch


class ServiceConfig(BaseModel):
    """Server-level configuration"""
    model_name: str = "CosyVoice-300M-SFT"  # Official CosyVoice model (SFT recommended)
    model_path: str = "pretrained_models/CosyVoice-300M-SFT"  # Local model path (downloaded via ModelScope)
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"  # Set to "debug" for detailed model loading logs
    max_text_length: int = 5000  # Maximum text length in characters
    
    # ModelScope configuration (for auto-download)
    use_modelscope: bool = True  # Auto-download from ModelScope if model not found locally
    modelscope_model_id: str = "iic/CosyVoice-300M-SFT"  # ModelScope model ID for download


class AudioConfig(BaseModel):
    """Audio output configuration - client configurable"""
    sample_rate: int = Field(default=24000, description="Output audio sample rate in Hz (CosyVoice default: 24000)")
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
    """Voice and style configuration"""
    speaker: str = Field(
        default="default",
        description="Speaker voice ID or name. Use 'list_voices' endpoint to get available voices."
    )
    style: Optional[str] = Field(
        default=None,
        description="Speaking style/emotion (e.g., 'cheerful', 'sad', 'angry', 'neutral')"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech rate multiplier (0.5=slow, 1.0=normal, 2.0=fast)"
    )
    pitch: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Pitch multiplier (0.5=low, 1.0=normal, 2.0=high)"
    )
    energy: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Energy/volume multiplier"
    )


class StreamingConfig(BaseModel):
    """
    Streaming configuration - ElevenLabs-style settings
    For production-ready low-latency streaming
    """
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
        description="Number of text sentences to accumulate before flushing audio (ElevenLabs-style)"
    )
    optimize_streaming_latency: int = Field(
        default=2,
        ge=0,
        le=4,
        description="Latency optimization level (0=quality, 4=fastest). Similar to ElevenLabs latency setting."
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
    """
    Text-to-speech synthesis configuration - ElevenLabs-inspired
    """
    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Stability setting (0=more variable/expressive, 1=more stable/consistent)"
    )
    similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Similarity boost for voice cloning (0=more creative, 1=more similar to original)"
    )
    use_speaker_boost: bool = Field(
        default=True,
        description="Enable speaker characteristics enhancement"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for synthesis randomness"
    )
    top_k: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Top-K sampling parameter"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-P (nucleus) sampling parameter"
    )
    repetition_penalty: float = Field(
        default=1.0,
        ge=1.0,
        le=2.0,
        description="Penalty for repeating tokens"
    )
    max_new_tokens: int = Field(
        default=2048,
        ge=256,
        le=4096,
        description="Maximum number of tokens to generate"
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
                    "sample_rate": 24000,
                    "channels": 1,
                    "encoding": "pcm_s16le"
                },
                "voice": {
                    "speaker": "default",
                    "speed": 1.0,
                    "pitch": 1.0
                },
                "streaming": {
                    "enabled": True,
                    "chunk_size": 1024,
                    "flush_threshold": 3,
                    "optimize_streaming_latency": 2
                },
                "synthesis": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "temperature": 0.7
                },
                "text_processing": {
                    "normalize_text": True,
                    "split_sentences": True
                }
            }
        }


# Default service configuration
SERVICE_CONFIG = ServiceConfig()

