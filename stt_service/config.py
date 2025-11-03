#!/usr/bin/env python3
"""
Configuration models for STT service
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
import torch


class ServiceConfig(BaseModel):
    """Server-level configuration"""
    model_name: str = "large-v3-turbo"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type: str = "float16" if torch.cuda.is_available() else "int8"
    host: str = "0.0.0.0"
    port: int = 8001
    model_cache_dir: str = "./models"
    log_level: str = "info"


class AudioConfig(BaseModel):
    """Audio format configuration - client configurable"""
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels (1=mono, 2=stereo)")
    encoding: Literal["pcm_s16le", "pcm_f32le", "mulaw", "alaw"] = Field(
        default="pcm_s16le",
        description="Audio encoding format"
    )
    chunk_size: Optional[int] = Field(
        default=None,
        description="Expected chunk size in bytes (optional)"
    )
    
    @property
    def bytes_per_sample(self) -> int:
        """Get bytes per sample based on encoding"""
        if self.encoding == "pcm_s16le":
            return 2
        elif self.encoding == "pcm_f32le":
            return 4
        elif self.encoding in ["mulaw", "alaw"]:
            return 1
        return 2


class VADConfig(BaseModel):
    """Voice Activity Detection configuration - client configurable"""
    enabled: bool = Field(default=True, description="Enable/disable VAD")
    mode: int = Field(default=3, ge=0, le=3, description="VAD aggressiveness (0-3, 3=most aggressive)")
    silence_duration: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Seconds of silence to trigger end of utterance"
    )
    min_speech_duration: float = Field(
        default=0.3,
        ge=0.1,
        le=2.0,
        description="Minimum speech duration in seconds to process"
    )
    frame_duration: int = Field(
        default=30,
        description="Frame duration in milliseconds (10, 20, or 30)"
    )
    speech_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Ratio of speech frames to trigger speech detection"
    )
    
    def validate_frame_duration(self) -> bool:
        """Validate frame duration is supported by WebRTC VAD"""
        return self.frame_duration in [10, 20, 30]


class TranscriptionConfig(BaseModel):
    """Transcription configuration - client configurable"""
    language: Optional[str] = Field(default=None, description="Language code (e.g., 'en', 'es', 'fr'). None for auto-detect")
    task: Literal["transcribe", "translate"] = Field(
        default="transcribe",
        description="Task: transcribe or translate to English"
    )
    beam_size: int = Field(default=5, ge=1, le=10, description="Beam size for decoding")
    best_of: int = Field(default=5, ge=1, le=10, description="Number of candidates when sampling")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Temperature for sampling")
    vad_filter: bool = Field(default=False, description="Use Whisper's internal VAD filter")
    condition_on_previous_text: bool = Field(
        default=False,
        description="Condition on previous text for context"
    )
    no_speech_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Threshold for no speech detection"
    )
    enable_partial_transcripts: bool = Field(
        default=True,
        description="Send partial transcripts while speaking"
    )
    partial_interval: float = Field(
        default=0.5,
        ge=0.1,
        le=2.0,
        description="Interval in seconds between partial transcripts"
    )


class SessionConfig(BaseModel):
    """Complete session configuration combining all configs"""
    audio: AudioConfig = Field(default_factory=AudioConfig)
    vad: VADConfig = Field(default_factory=VADConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "encoding": "pcm_s16le"
                },
                "vad": {
                    "enabled": True,
                    "mode": 3,
                    "silence_duration": 1.0,
                    "min_speech_duration": 0.3
                },
                "transcription": {
                    "language": "en",
                    "enable_partial_transcripts": True,
                    "partial_interval": 0.5
                }
            }
        }


# Default service configuration
SERVICE_CONFIG = ServiceConfig()

