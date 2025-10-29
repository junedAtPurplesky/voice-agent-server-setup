"""
STT Models and Processors
Handles Whisper model loading, audio processing, and transcription
"""

import os
import tempfile
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment
import librosa
import soundfile as sf
from .config import config_manager, LanguageCode, TranscriptionConfig

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Audio processing utilities"""
    
    @staticmethod
    def validate_audio_file(file_path: str, max_size_mb: int) -> bool:
        """Validate audio file format and size"""
        try:
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > max_size_mb:
                logger.warning(f"File size {file_size_mb:.2f}MB exceeds limit {max_size_mb}MB")
                return False
            
            # Try to load audio file
            audio, sr = librosa.load(file_path, sr=None)
            if len(audio) == 0:
                logger.warning("Audio file is empty")
                return False
            
            logger.info(f"Audio file validated: {file_size_mb:.2f}MB, {sr}Hz, {len(audio)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False
    
    @staticmethod
    def preprocess_audio(file_path: str, target_sr: int = 16000) -> str:
        """Preprocess audio file for Whisper"""
        try:
            # Load audio
            audio, sr = librosa.load(file_path, sr=target_sr)
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            # Create temporary file for processed audio
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(temp_file.name, audio, target_sr)
            
            logger.info(f"Audio preprocessed: {target_sr}Hz, {len(audio)} samples")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")


class STTModel:
    """Speech-to-Text model wrapper"""
    
    def __init__(self):
        self.model = None
        self.config = config_manager.get_config()
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading {self.config.model.name} model on {self.config.model.device}...")
            self.model = WhisperModel(
                self.config.model.name,
                device=self.config.model.device,
                compute_type=self.config.model.compute_type,
                download_root=self.config.model.download_root,
                local_files_only=self.config.model.local_files_only
            )
            logger.info("✅ STT model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def transcribe_file(
        self, 
        file_path: str, 
        config: Optional[TranscriptionConfig] = None
    ) -> Tuple[List[Segment], Dict[str, Any]]:
        """Transcribe audio file"""
        try:
            # Use provided config or default
            if config is None:
                config = self.config.transcription
            
            # Get transcription parameters
            params = self._get_transcription_params(config)
            
            logger.info(f"Transcribing file: {file_path}")
            logger.debug(f"Transcription params: {params}")
            
            # Transcribe
            segments, info = self.model.transcribe(file_path, **params)
            
            # Convert generator to list
            segment_list = list(segments)
            
            logger.info(f"✅ Transcription complete: {len(segment_list)} segments")
            return segment_list, info
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise
    
    def transcribe_stream(
        self, 
        audio_data: bytes, 
        config: Optional[TranscriptionConfig] = None
    ) -> Tuple[List[Segment], Dict[str, Any]]:
        """Transcribe audio stream data"""
        try:
            # Create temporary file for audio data
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.write(audio_data)
            temp_file.close()
            
            try:
                # Transcribe using file method
                return self.transcribe_file(temp_file.name, config)
            finally:
                # Clean up temp file
                AudioProcessor.cleanup_temp_file(temp_file.name)
                
        except Exception as e:
            logger.error(f"❌ Stream transcription failed: {e}")
            raise
    
    def _get_transcription_params(self, config: TranscriptionConfig) -> Dict[str, Any]:
        """Get transcription parameters from config"""
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
            params["vad_parameters"] = {
                "threshold": config.vad_config.threshold,
                "min_speech_duration_ms": config.vad_config.min_speech_duration_ms,
                "min_silence_duration_ms": config.vad_config.min_silence_duration_ms,
                "speech_pad_ms": config.vad_config.speech_pad_ms
            }
        
        return params


class TranscriptionResult:
    """Transcription result container"""
    
    def __init__(
        self, 
        segments: List[Segment], 
        info: Dict[str, Any], 
        config: TranscriptionConfig,
        processing_time: float
    ):
        self.segments = segments
        self.info = info
        self.config = config
        self.processing_time = processing_time
        self.timestamp = datetime.utcnow()
    
    @property
    def full_text(self) -> str:
        """Get full transcribed text"""
        return "".join(segment.text for segment in self.segments)
    
    @property
    def segments_data(self) -> List[Dict[str, Any]]:
        """Get segments as dictionary list"""
        return [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "confidence": getattr(segment, 'confidence', 0.0),
                "words": getattr(segment, 'words', [])
            }
            for segment in self.segments
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": True,
            "text": self.full_text,
            "language": self.config.language.value,
            "duration": self.info.get("duration", 0.0),
            "segments": self.segments_data,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat(),
            "config": {
                "vad_enabled": self.config.vad_config.enabled,
                "beam_size": self.config.beam_size,
                "temperature": self.config.temperature
            }
        }


class STTProcessor:
    """Main STT processing class"""
    
    def __init__(self):
        self.model = STTModel()
        self.audio_processor = AudioProcessor()
        self.config = config_manager.get_config()
    
    async def process_file(
        self, 
        file_path: str, 
        config: Optional[TranscriptionConfig] = None
    ) -> TranscriptionResult:
        """Process audio file for transcription"""
        start_time = datetime.utcnow()
        
        try:
            # Validate audio file
            if not self.audio_processor.validate_audio_file(file_path, self.config.max_file_size_mb):
                raise ValueError("Invalid audio file")
            
            # Preprocess audio
            processed_file = self.audio_processor.preprocess_audio(file_path)
            
            try:
                # Transcribe
                segments, info = self.model.transcribe_file(processed_file, config)
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Create result
                result = TranscriptionResult(segments, info, config or self.config.transcription, processing_time)
                
                logger.info(f"✅ File processing complete: {processing_time:.2f}s")
                return result
                
            finally:
                # Clean up processed file
                self.audio_processor.cleanup_temp_file(processed_file)
                
        except Exception as e:
            logger.error(f"❌ File processing failed: {e}")
            raise
    
    async def process_stream(
        self, 
        audio_data: bytes, 
        config: Optional[TranscriptionConfig] = None
    ) -> TranscriptionResult:
        """Process audio stream for transcription"""
        start_time = datetime.utcnow()
        
        try:
            # Transcribe stream
            segments, info = self.model.transcribe_stream(audio_data, config)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            result = TranscriptionResult(segments, info, config or self.config.transcription, processing_time)
            
            logger.info(f"✅ Stream processing complete: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Stream processing failed: {e}")
            raise


# Global STT processor instance
stt_processor = STTProcessor()

