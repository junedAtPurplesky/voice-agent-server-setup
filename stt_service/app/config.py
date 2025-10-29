"""
Configuration management for STT service
Handles dynamic configuration for VAD, language selection, and model settings
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LanguageCode(str, Enum):
    """Supported language codes"""
    AUTO = "auto"
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ITALIAN = "it"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    TURKISH = "tr"
    GREEK = "el"
    HEBREW = "he"
    THAI = "th"
    VIETNAMESE = "vi"
    INDONESIAN = "id"
    MALAY = "ms"
    TAGALOG = "tl"
    BENGALI = "bn"
    TAMIL = "ta"
    TELUGU = "te"
    MARATHI = "mr"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    URDU = "ur"


class VADConfig(BaseModel):
    """Voice Activity Detection configuration"""
    enabled: bool = Field(default=True, description="Enable VAD filtering")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="VAD threshold (0.0-1.0)")
    min_speech_duration_ms: int = Field(default=250, ge=0, description="Minimum speech duration in milliseconds")
    min_silence_duration_ms: int = Field(default=200, ge=0, description="Minimum silence duration in milliseconds")
    speech_pad_ms: int = Field(default=400, ge=0, description="Speech padding in milliseconds")


class TranscriptionConfig(BaseModel):
    """Transcription configuration"""
    language: LanguageCode = Field(default=LanguageCode.AUTO, description="Language code for transcription")
    vad_config: VADConfig = Field(default_factory=VADConfig, description="VAD configuration")
    beam_size: int = Field(default=5, ge=1, le=20, description="Beam size for beam search")
    best_of: int = Field(default=5, ge=1, le=20, description="Number of candidates to consider")
    patience: float = Field(default=1.0, ge=0.0, le=10.0, description="Patience for beam search")
    length_penalty: float = Field(default=1.0, ge=0.0, le=2.0, description="Length penalty")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Temperature for sampling")
    compression_ratio_threshold: float = Field(default=2.4, ge=0.0, le=10.0, description="Compression ratio threshold")
    log_prob_threshold: float = Field(default=-1.0, ge=-10.0, le=0.0, description="Log probability threshold")
    no_speech_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="No speech threshold")
    condition_on_previous_text: bool = Field(default=True, description="Condition on previous text")
    prompt_reset_on_temperature: float = Field(default=0.5, ge=0.0, le=1.0, description="Prompt reset on temperature")
    initial_prompt: Optional[str] = Field(default=None, description="Initial prompt for transcription")
    word_timestamps: bool = Field(default=False, description="Include word-level timestamps")
    prepend_punctuations: str = Field(default="\"'([{-", description="Prepend punctuations")
    append_punctuations: str = Field(default="\"'.,:)]}", description="Append punctuations")


class ModelConfig(BaseModel):
    """Model configuration"""
    name: str = Field(default="large-v3-turbo", description="Model name")
    device: str = Field(default="cuda", description="Device to run on (cuda/cpu)")
    compute_type: str = Field(default="int8", description="Compute type (int8/float16/float32)")
    download_root: Optional[str] = Field(default=None, description="Download root directory")
    local_files_only: bool = Field(default=False, description="Use only local files")


class STTConfig(BaseModel):
    """Main STT service configuration"""
    model: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig, description="Transcription configuration")
    api_key: str = Field(default="stt_secret_key_production_123456", description="API key for authentication")
    max_file_size_mb: int = Field(default=100, ge=1, le=1000, description="Maximum file size in MB")
    supported_formats: list = Field(default=["wav", "mp3", "m4a", "flac", "ogg"], description="Supported audio formats")
    chunk_size_bytes: int = Field(default=32000, ge=1024, le=1024000, description="WebSocket chunk size in bytes")
    max_websocket_connections: int = Field(default=100, ge=1, le=1000, description="Maximum WebSocket connections")
    request_timeout_seconds: int = Field(default=300, ge=10, le=3600, description="Request timeout in seconds")


class ConfigManager:
    """Configuration manager for STT service"""
    
    def __init__(self):
        self._config = self._load_config()
    
    def _load_config(self) -> STTConfig:
        """Load configuration from environment variables"""
        return STTConfig(
            model=ModelConfig(
                name=os.getenv("STT_MODEL_NAME", "large-v3-turbo"),
                device=os.getenv("STT_DEVICE", "cuda"),
                compute_type=os.getenv("STT_COMPUTE_TYPE", "int8"),
                download_root=os.getenv("STT_DOWNLOAD_ROOT"),
                local_files_only=os.getenv("STT_LOCAL_FILES_ONLY", "false").lower() == "true"
            ),
            transcription=TranscriptionConfig(
                language=LanguageCode(os.getenv("STT_DEFAULT_LANGUAGE", "auto")),
                vad_config=VADConfig(
                    enabled=os.getenv("STT_VAD_ENABLED", "true").lower() == "true",
                    threshold=float(os.getenv("STT_VAD_THRESHOLD", "0.5")),
                    min_speech_duration_ms=int(os.getenv("STT_VAD_MIN_SPEECH_DURATION_MS", "250")),
                    min_silence_duration_ms=int(os.getenv("STT_VAD_MIN_SILENCE_DURATION_MS", "200")),
                    speech_pad_ms=int(os.getenv("STT_VAD_SPEECH_PAD_MS", "400"))
                ),
                beam_size=int(os.getenv("STT_BEAM_SIZE", "5")),
                best_of=int(os.getenv("STT_BEST_OF", "5")),
                patience=float(os.getenv("STT_PATIENCE", "1.0")),
                length_penalty=float(os.getenv("STT_LENGTH_PENALTY", "1.0")),
                temperature=float(os.getenv("STT_TEMPERATURE", "0.0")),
                compression_ratio_threshold=float(os.getenv("STT_COMPRESSION_RATIO_THRESHOLD", "2.4")),
                log_prob_threshold=float(os.getenv("STT_LOG_PROB_THRESHOLD", "-1.0")),
                no_speech_threshold=float(os.getenv("STT_NO_SPEECH_THRESHOLD", "0.6")),
                condition_on_previous_text=os.getenv("STT_CONDITION_ON_PREVIOUS_TEXT", "true").lower() == "true",
                prompt_reset_on_temperature=float(os.getenv("STT_PROMPT_RESET_ON_TEMPERATURE", "0.5")),
                initial_prompt=os.getenv("STT_INITIAL_PROMPT"),
                word_timestamps=os.getenv("STT_WORD_TIMESTAMPS", "false").lower() == "true",
                prepend_punctuations=os.getenv("STT_PREPEND_PUNCTUATIONS", "\"'([{-"),
                append_punctuations=os.getenv("STT_APPEND_PUNCTUATIONS", "\"'.,:)]}")
            ),
            api_key=os.getenv("STT_API_KEY", "stt_secret_key_production_123456"),
            max_file_size_mb=int(os.getenv("STT_MAX_FILE_SIZE_MB", "100")),
            supported_formats=os.getenv("STT_SUPPORTED_FORMATS", "wav,mp3,m4a,flac,ogg").split(","),
            chunk_size_bytes=int(os.getenv("STT_CHUNK_SIZE_BYTES", "32000")),
            max_websocket_connections=int(os.getenv("STT_MAX_WEBSOCKET_CONNECTIONS", "100")),
            request_timeout_seconds=int(os.getenv("STT_REQUEST_TIMEOUT_SECONDS", "300"))
        )
    
    def get_config(self) -> STTConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, **kwargs) -> STTConfig:
        """Update configuration with new values"""
        config_dict = self._config.dict()
        config_dict.update(kwargs)
        self._config = STTConfig(**config_dict)
        return self._config
    
    def get_vad_config(self) -> Dict[str, Any]:
        """Get VAD configuration as dictionary for Whisper"""
        vad_config = self._config.transcription.vad_config
        return {
            "threshold": vad_config.threshold,
            "min_speech_duration_ms": vad_config.min_speech_duration_ms,
            "min_silence_duration_ms": vad_config.min_silence_duration_ms,
            "speech_pad_ms": vad_config.speech_pad_ms
        }
    
    def get_transcription_params(self) -> Dict[str, Any]:
        """Get transcription parameters as dictionary for Whisper"""
        config = self._config.transcription
        params = {
            "language": config.language.value if config.language != LanguageCode.AUTO else None,
            "beam_size": config.beam_size,
            "best_of": config.best_of,
            "patience": config.patience,
            "length_penalty": config.length_penalty,
            "temperature": config.temperature,
            "compression_ratio_threshold": config.compression_ratio_threshold,
            "log_prob_threshold": config.log_prob_threshold,
            "no_speech_threshold": config.no_speech_threshold,
            "condition_on_previous_text": config.condition_on_previous_text,
            "prompt_reset_on_temperature": config.prompt_reset_on_temperature,
            "word_timestamps": config.word_timestamps,
            "prepend_punctuations": config.prepend_punctuations,
            "append_punctuations": config.append_punctuations
        }
        
        if config.initial_prompt:
            params["initial_prompt"] = config.initial_prompt
        
        if config.vad_config.enabled:
            params["vad_filter"] = True
            params["vad_parameters"] = self.get_vad_config()
        
        return params


# Global configuration instance
config_manager = ConfigManager()

