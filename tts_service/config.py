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
    
    # Authentication configuration (Production)
    require_auth: bool = Field(
        default=False,
        description="Require API key authentication (set TTS_REQUIRE_AUTH=true in production)"
    )
    api_keys: List[str] = Field(
        default_factory=list,
        description="List of valid API keys (set via TTS_API_KEYS env var, comma-separated)"
    )
    
    # ModelScope configuration (for auto-download)
    use_modelscope: bool = True  # Auto-download from ModelScope if model not found locally
    modelscope_model_id: str = "iic/CosyVoice-300M-SFT"  # ModelScope model ID for download
    
    # Model integrity checking
    verify_model_integrity: bool = True  # Verify all required files are present before loading
    auto_repair_model: bool = True  # Automatically re-download if model is incomplete
    
    # Required model files for verification (can be overridden for different models)
    required_model_files: list = [
        'speech_tokenizer_v1.onnx',
        'campplus.onnx', 
        'flow.decoder.estimator.fp32.onnx',
        'cosyvoice.yaml',
        'flow.pt',
        'hift.pt'
    ]


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
# Load from .env file and environment variables
import os
from pathlib import Path
import logging

# Initialize logger for config loading
logger = logging.getLogger(__name__)

# Try to load python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    # Load .env file from the same directory as this config file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        # Try to load from current working directory
        load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env file loading
    logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")
    logger.warning("Environment variables will only be loaded from system environment")

def load_service_config() -> ServiceConfig:
    """Load service configuration from .env file and environment variables"""
    config = ServiceConfig()
    
    # Override with environment variables if present
    require_auth_env = os.getenv("TTS_REQUIRE_AUTH", "").lower()
    if require_auth_env in ("true", "1", "yes", "on"):
        config.require_auth = True
        logger.info("Authentication is REQUIRED (TTS_REQUIRE_AUTH=true)")
    else:
        logger.info("Authentication is OPTIONAL (TTS_REQUIRE_AUTH not set or false)")
    
    # Load API keys from environment (comma-separated)
    api_keys_env = os.getenv("TTS_API_KEYS", "")
    if api_keys_env:
        config.api_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
        logger.info(f"Loaded {len(config.api_keys)} API key(s) from environment")
    
    # Override ALL config values from environment if present
    # Server configuration
    if os.getenv("TTS_HOST"):
        config.host = os.getenv("TTS_HOST")
    if os.getenv("TTS_PORT"):
        config.port = int(os.getenv("TTS_PORT"))
    if os.getenv("TTS_LOG_LEVEL"):
        config.log_level = os.getenv("TTS_LOG_LEVEL")
    if os.getenv("TTS_MAX_TEXT_LENGTH"):
        config.max_text_length = int(os.getenv("TTS_MAX_TEXT_LENGTH"))
    
    # Model configuration
    if os.getenv("TTS_MODEL_NAME"):
        config.model_name = os.getenv("TTS_MODEL_NAME")
    if os.getenv("TTS_MODEL_PATH"):
        config.model_path = os.getenv("TTS_MODEL_PATH")
    if os.getenv("TTS_DEVICE"):
        device_env = os.getenv("TTS_DEVICE").lower()
        if device_env == "auto":
            config.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            config.device = device_env
    
    # ModelScope configuration
    if os.getenv("TTS_USE_MODELSCOPE"):
        use_modelscope_env = os.getenv("TTS_USE_MODELSCOPE", "").lower()
        config.use_modelscope = use_modelscope_env in ("true", "1", "yes", "on")
    if os.getenv("TTS_MODELSCOPE_MODEL_ID"):
        config.modelscope_model_id = os.getenv("TTS_MODELSCOPE_MODEL_ID")
    if os.getenv("TTS_VERIFY_MODEL_INTEGRITY"):
        verify_env = os.getenv("TTS_VERIFY_MODEL_INTEGRITY", "").lower()
        config.verify_model_integrity = verify_env in ("true", "1", "yes", "on")
    if os.getenv("TTS_AUTO_REPAIR_MODEL"):
        auto_repair_env = os.getenv("TTS_AUTO_REPAIR_MODEL", "").lower()
        config.auto_repair_model = auto_repair_env in ("true", "1", "yes", "on")
    
    # Warn if auth is required but no keys provided
    if config.require_auth and not config.api_keys:
        logger.warning("WARNING: Authentication is required but no API keys provided!")
        logger.warning("Set TTS_API_KEYS in .env file or environment variable")
    
    return config

SERVICE_CONFIG = load_service_config()

