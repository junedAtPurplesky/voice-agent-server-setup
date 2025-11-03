#!/usr/bin/env python3
"""
Transcription engine using Faster Whisper
"""

import time
import logging
from typing import Dict, Any, Optional

import numpy as np
from faster_whisper import WhisperModel

from config import ServiceConfig, TranscriptionConfig

logger = logging.getLogger(__name__)


class TranscriptionResult:
    """Result of transcription"""
    def __init__(
        self,
        text: str,
        segments: list,
        language: str,
        language_probability: float,
        processing_time: float,
        audio_duration: float
    ):
        self.text = text
        self.segments = segments
        self.language = language
        self.language_probability = language_probability
        self.processing_time = processing_time
        self.audio_duration = audio_duration
        self.realtime_factor = processing_time / audio_duration if audio_duration > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "segments": self.segments,
            "language": self.language,
            "language_probability": self.language_probability,
            "processing_time": self.processing_time,
            "audio_duration": self.audio_duration,
            "realtime_factor": self.realtime_factor
        }


class TranscriptionEngine:
    """Handles Whisper model loading and transcription"""
    
    def __init__(self, service_config: ServiceConfig):
        self.service_config = service_config
        self.model: Optional[WhisperModel] = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.service_config.model_name}")
            logger.info(f"Device: {self.service_config.device}")
            logger.info(f"Compute type: {self.service_config.compute_type}")
            
            self.model = WhisperModel(
                self.service_config.model_name,
                device=self.service_config.device,
                compute_type=self.service_config.compute_type,
                download_root=self.service_config.model_cache_dir
            )
            
            logger.info("Model loaded successfully")
            
            # Warm up the model
            self._warmup()
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _warmup(self):
        """Warm up the model with dummy audio"""
        try:
            logger.info("Warming up model...")
            dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
            self.transcribe(dummy_audio, TranscriptionConfig())
            logger.info("Model warmed up")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
    
    def transcribe(
        self,
        audio_data: np.ndarray,
        config: TranscriptionConfig
    ) -> TranscriptionResult:
        """
        Transcribe audio using Faster Whisper
        
        Args:
            audio_data: Audio numpy array (float32, normalized to [-1, 1])
            config: Transcription configuration
            
        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        try:
            start_time = time.time()
            audio_duration = len(audio_data) / 16000.0  # Assuming 16kHz
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_data,
                language=config.language,
                task=config.task,
                beam_size=config.beam_size,
                best_of=config.best_of,
                temperature=config.temperature,
                vad_filter=config.vad_filter,
                condition_on_previous_text=config.condition_on_previous_text,
                no_speech_threshold=config.no_speech_threshold
            )
            
            # Collect segments
            text_segments = []
            full_text = ""
            
            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                text_segments.append(segment_dict)
                full_text += segment.text.strip() + " "
            
            processing_time = time.time() - start_time
            
            result = TranscriptionResult(
                text=full_text.strip(),
                segments=text_segments,
                language=info.language,
                language_probability=info.language_probability,
                processing_time=processing_time,
                audio_duration=audio_duration
            )
            
            logger.debug(
                f"Transcribed {audio_duration:.2f}s in {processing_time:.3f}s "
                f"(RTF: {result.realtime_factor:.2f}x)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.service_config.model_name,
            "device": self.service_config.device,
            "compute_type": self.service_config.compute_type
        }

