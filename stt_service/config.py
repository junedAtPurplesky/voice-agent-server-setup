#!/usr/bin/env python3
"""
Configuration models for Speechmatics-compatible STT service
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field
import torch
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to load python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")


class ServiceConfig(BaseModel):
    """Server-level configuration"""
    model_name: str = "large-v3"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type: str = "float16" if torch.cuda.is_available() else "int8"
    host: str = "0.0.0.0"
    port: int = 8001
    model_cache_dir: str = "./models"
    log_level: str = "info"
    
    # Authentication configuration (Speechmatics-style)
    require_auth: bool = Field(
        default=False,
        description="Require API key authentication (set STT_REQUIRE_AUTH=true in production)"
    )
    api_keys: List[str] = Field(
        default_factory=list,
        description="List of valid API keys (set via STT_API_KEYS env var, comma-separated)"
    )


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
    """Voice Activity Detection configuration - Silero VAD"""
    enabled: bool = Field(default=True, description="Enable/disable VAD")
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="VAD threshold (0.0-1.0, higher = more aggressive)"
    )
    min_speech_duration_ms: int = Field(
        default=250,
        ge=100,
        le=2000,
        description="Minimum speech duration in milliseconds"
    )
    min_silence_duration_ms: int = Field(
        default=100,
        ge=50,
        le=1000,
        description="Minimum silence duration in milliseconds"
    )
    speech_pad_ms: int = Field(
        default=400,
        ge=0,
        le=2000,
        description="Padding to add around speech segments in milliseconds"
    )
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate for VAD processing"
    )


class TranscriptionConfig(BaseModel):
    """Transcription configuration - Speechmatics-compatible"""
    language: Optional[str] = Field(default=None, description="Language code (e.g., 'en', 'es', 'fr'). None for auto-detect")
    output_format: Literal["json", "text"] = Field(
        default="json",
        description="Output format: json or text"
    )
    enable_partials: bool = Field(
        default=True,
        description="Enable partial transcripts (Speechmatics-style)"
    )
    max_delay: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Maximum delay for partial results in seconds"
    )
    # Whisper-specific options
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


def load_service_config() -> ServiceConfig:
    """Load service configuration from environment variables"""
    config = ServiceConfig()
    
    # Override with environment variables if present
    require_auth_env = os.getenv("STT_REQUIRE_AUTH", "").lower()
    if require_auth_env in ("true", "1", "yes", "on"):
        config.require_auth = True
        logger.info("Authentication is REQUIRED (STT_REQUIRE_AUTH=true)")
    else:
        logger.info("Authentication is OPTIONAL (STT_REQUIRE_AUTH not set or false)")
    
    # Load API keys from environment (comma-separated)
    api_keys_env = os.getenv("STT_API_KEYS", "")
    if api_keys_env:
        config.api_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
        logger.info(f"Loaded {len(config.api_keys)} API key(s) from environment")
    
    # Override config values from environment
    if os.getenv("STT_HOST"):
        config.host = os.getenv("STT_HOST")
    if os.getenv("STT_PORT"):
        config.port = int(os.getenv("STT_PORT"))
    if os.getenv("STT_LOG_LEVEL"):
        config.log_level = os.getenv("STT_LOG_LEVEL")
    if os.getenv("STT_MODEL_NAME"):
        config.model_name = os.getenv("STT_MODEL_NAME")
    if os.getenv("STT_DEVICE"):
        device_env = os.getenv("STT_DEVICE").lower()
        if device_env == "auto":
            config.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            config.device = device_env
    if os.getenv("STT_COMPUTE_TYPE"):
        config.compute_type = os.getenv("STT_COMPUTE_TYPE")
    if os.getenv("STT_MODEL_CACHE_DIR"):
        config.model_cache_dir = os.getenv("STT_MODEL_CACHE_DIR")
    
    # Warn if auth is required but no keys provided
    if config.require_auth and not config.api_keys:
        logger.warning("WARNING: Authentication is required but no API keys provided!")
        logger.warning("Set STT_API_KEYS in .env file or environment variable")
    
    return config

# Default service configuration
SERVICE_CONFIG = load_service_config()

