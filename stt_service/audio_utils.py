#!/usr/bin/env python3
"""
Audio format conversion and processing utilities
"""

import struct
import audioop
import numpy as np
from typing import Optional
import logging

from config import AudioConfig

logger = logging.getLogger(__name__)


class AudioConverter:
    """Handles audio format conversion and normalization"""
    
    def __init__(self, audio_config: AudioConfig):
        self.config = audio_config
        
    def convert_to_pcm16(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio to 16-bit PCM format
        
        Args:
            audio_bytes: Input audio bytes in configured format
            
        Returns:
            Audio in 16-bit PCM format
        """
        if self.config.encoding == "pcm_s16le":
            # Already in correct format
            return audio_bytes
            
        elif self.config.encoding == "pcm_f32le":
            # Convert float32 to int16
            return self._float32_to_int16(audio_bytes)
            
        elif self.config.encoding == "mulaw":
            # Convert mu-law to linear PCM
            return audioop.ulaw2lin(audio_bytes, 2)
            
        elif self.config.encoding == "alaw":
            # Convert A-law to linear PCM
            return audioop.alaw2lin(audio_bytes, 2)
            
        else:
            logger.warning(f"Unknown encoding {self.config.encoding}, assuming PCM16")
            return audio_bytes
    
    def convert_to_mono(self, audio_bytes: bytes) -> bytes:
        """
        Convert stereo audio to mono
        
        Args:
            audio_bytes: Input audio bytes (must be PCM16)
            
        Returns:
            Mono audio in PCM16 format
        """
        if self.config.channels == 1:
            return audio_bytes
            
        # Convert stereo to mono by averaging channels
        return audioop.tomono(audio_bytes, 2, 0.5, 0.5)
    
    def resample(self, audio_bytes: bytes, target_rate: int = 16000) -> bytes:
        """
        Resample audio to target sample rate
        
        Args:
            audio_bytes: Input audio bytes (must be PCM16 mono)
            target_rate: Target sample rate
            
        Returns:
            Resampled audio
        """
        if self.config.sample_rate == target_rate:
            return audio_bytes
            
        # Calculate ratio
        ratio = target_rate / self.config.sample_rate
        
        # Use audioop.ratecv for resampling
        resampled, _ = audioop.ratecv(
            audio_bytes,
            2,  # 16-bit = 2 bytes
            1,  # mono
            self.config.sample_rate,
            target_rate,
            None
        )
        
        return resampled
    
    def normalize_audio(self, audio_bytes: bytes) -> bytes:
        """
        Complete audio normalization pipeline:
        1. Convert to PCM16
        2. Convert to mono
        3. Resample to 16kHz
        
        Args:
            audio_bytes: Input audio in configured format
            
        Returns:
            Normalized audio (PCM16, mono, 16kHz)
        """
        # Step 1: Convert encoding
        audio_bytes = self.convert_to_pcm16(audio_bytes)
        
        # Step 2: Convert to mono
        audio_bytes = self.convert_to_mono(audio_bytes)
        
        # Step 3: Resample to 16kHz
        audio_bytes = self.resample(audio_bytes, 16000)
        
        return audio_bytes
    
    def to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convert audio bytes to numpy array for Whisper
        
        Args:
            audio_bytes: Input audio (must be PCM16, mono, 16kHz)
            
        Returns:
            Numpy array normalized to [-1, 1]
        """
        # Convert to int16 array
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Normalize to float32 in range [-1, 1]
        audio_np = audio_np.astype(np.float32) / 32768.0
        
        return audio_np
    
    @staticmethod
    def _float32_to_int16(audio_bytes: bytes) -> bytes:
        """Convert float32 PCM to int16 PCM"""
        # Unpack float32 samples
        num_samples = len(audio_bytes) // 4
        float_samples = struct.unpack(f'<{num_samples}f', audio_bytes)
        
        # Convert to int16
        int16_samples = [int(max(-1.0, min(1.0, s)) * 32767) for s in float_samples]
        
        # Pack as int16
        return struct.pack(f'<{num_samples}h', *int16_samples)
    
    def get_duration(self, audio_bytes: bytes) -> float:
        """
        Calculate audio duration in seconds
        
        Args:
            audio_bytes: Audio bytes in configured format
            
        Returns:
            Duration in seconds
        """
        bytes_per_sample = self.config.bytes_per_sample
        total_samples = len(audio_bytes) // (bytes_per_sample * self.config.channels)
        return total_samples / self.config.sample_rate

