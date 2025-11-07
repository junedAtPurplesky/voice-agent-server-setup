#!/usr/bin/env python3
"""
Audio format conversion and processing utilities for TTS output
"""

import struct
import audioop
import io
import wave
import numpy as np
from typing import Optional, Tuple
import logging

from config import AudioConfig

logger = logging.getLogger(__name__)


class AudioConverter:
    """Handles audio format conversion and encoding for TTS output"""
    
    def __init__(self, audio_config: AudioConfig):
        self.config = audio_config
        
    def numpy_to_pcm16(self, audio_np: np.ndarray) -> bytes:
        """
        Convert numpy array to 16-bit PCM bytes
        
        Args:
            audio_np: Input audio as numpy array (float32, normalized to [-1, 1])
            
        Returns:
            Audio as 16-bit PCM bytes
        """
        # Clip to valid range
        audio_np = np.clip(audio_np, -1.0, 1.0)
        
        # Convert to int16
        audio_int16 = (audio_np * 32767).astype(np.int16)
        
        # Convert to bytes
        return audio_int16.tobytes()
    
    def numpy_to_pcm32(self, audio_np: np.ndarray) -> bytes:
        """
        Convert numpy array to 32-bit float PCM bytes
        
        Args:
            audio_np: Input audio as numpy array (float32)
            
        Returns:
            Audio as 32-bit float PCM bytes
        """
        # Clip to valid range
        audio_np = np.clip(audio_np, -1.0, 1.0)
        
        # Convert to bytes
        return audio_np.astype(np.float32).tobytes()
    
    def to_stereo(self, audio_bytes: bytes) -> bytes:
        """
        Convert mono audio to stereo
        
        Args:
            audio_bytes: Input mono audio bytes (PCM16)
            
        Returns:
            Stereo audio in PCM16 format
        """
        if self.config.channels == 1:
            return audio_bytes
        
        # Duplicate channel for stereo
        return audioop.tostereo(audio_bytes, 2, 1.0, 1.0)
    
    def resample(
        self,
        audio_bytes: bytes,
        source_rate: int,
        target_rate: Optional[int] = None
    ) -> bytes:
        """
        Resample audio to target sample rate
        
        Args:
            audio_bytes: Input audio bytes (PCM16)
            source_rate: Source sample rate
            target_rate: Target sample rate (uses config if None)
            
        Returns:
            Resampled audio
        """
        if target_rate is None:
            target_rate = self.config.sample_rate
            
        if source_rate == target_rate:
            return audio_bytes
        
        # Use audioop.ratecv for resampling
        channels = self.config.channels if self.config.channels > 1 else 1
        resampled, _ = audioop.ratecv(
            audio_bytes,
            2,  # 16-bit = 2 bytes
            channels,
            source_rate,
            target_rate,
            None
        )
        
        return resampled
    
    def convert_audio(
        self,
        audio_np: np.ndarray,
        source_sample_rate: int
    ) -> bytes:
        """
        Complete audio conversion pipeline for output:
        1. Convert numpy to PCM
        2. Resample to target rate
        3. Convert to stereo if needed
        4. Encode to target format
        
        Args:
            audio_np: Input audio as numpy array
            source_sample_rate: Source sample rate
            
        Returns:
            Encoded audio bytes in configured format
        """
        # Step 1: Convert to PCM16
        audio_bytes = self.numpy_to_pcm16(audio_np)
        
        # Step 2: Resample
        if source_sample_rate != self.config.sample_rate:
            # For resampling, we need mono first
            audio_bytes = self.resample(audio_bytes, source_sample_rate, self.config.sample_rate)
        
        # Step 3: Convert to stereo if needed
        if self.config.channels == 2:
            audio_bytes = self.to_stereo(audio_bytes)
        
        # Step 4: Encode to target format
        audio_bytes = self.encode_audio(audio_bytes)
        
        return audio_bytes
    
    def encode_audio(self, audio_bytes: bytes) -> bytes:
        """
        Encode audio to target format
        
        Args:
            audio_bytes: Input audio as PCM16 bytes
            
        Returns:
            Encoded audio bytes
        """
        if self.config.encoding == "pcm_s16le":
            return audio_bytes
            
        elif self.config.encoding == "pcm_f32le":
            # Convert int16 to float32
            return self._pcm16_to_float32(audio_bytes)
            
        elif self.config.encoding == "wav":
            # Wrap in WAV container
            return self._wrap_wav(audio_bytes)
            
        elif self.config.encoding == "mp3":
            # Would need pydub or similar for MP3 encoding
            logger.warning("MP3 encoding not yet implemented, using PCM16")
            return audio_bytes
            
        elif self.config.encoding == "opus":
            # Would need opuslib for Opus encoding
            logger.warning("Opus encoding not yet implemented, using PCM16")
            return audio_bytes
            
        else:
            logger.warning(f"Unknown encoding {self.config.encoding}, using PCM16")
            return audio_bytes
    
    def _pcm16_to_float32(self, audio_bytes: bytes) -> bytes:
        """Convert PCM16 to float32"""
        # Unpack int16 samples
        num_samples = len(audio_bytes) // 2
        int16_samples = struct.unpack(f'<{num_samples}h', audio_bytes)
        
        # Convert to float32
        float32_samples = [s / 32768.0 for s in int16_samples]
        
        # Pack as float32
        return struct.pack(f'<{num_samples}f', *float32_samples)
    
    def _wrap_wav(self, audio_bytes: bytes) -> bytes:
        """Wrap PCM audio in WAV container"""
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.config.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes(audio_bytes)
        
        return buffer.getvalue()
    
    def get_duration(self, audio_np: np.ndarray, sample_rate: int) -> float:
        """
        Calculate audio duration in seconds
        
        Args:
            audio_np: Audio numpy array
            sample_rate: Sample rate
            
        Returns:
            Duration in seconds
        """
        return len(audio_np) / sample_rate
    
    def apply_fade(
        self,
        audio_np: np.ndarray,
        fade_in_ms: int = 50,
        fade_out_ms: int = 50,
        sample_rate: int = 24000
    ) -> np.ndarray:
        """
        Apply fade in/out to audio
        
        Args:
            audio_np: Input audio
            fade_in_ms: Fade in duration in milliseconds
            fade_out_ms: Fade out duration in milliseconds
            sample_rate: Sample rate
            
        Returns:
            Audio with fades applied
        """
        audio_copy = audio_np.copy()
        
        # Fade in
        fade_in_samples = int(fade_in_ms * sample_rate / 1000)
        if fade_in_samples > 0 and fade_in_samples < len(audio_copy):
            fade_in_curve = np.linspace(0, 1, fade_in_samples)
            audio_copy[:fade_in_samples] *= fade_in_curve
        
        # Fade out
        fade_out_samples = int(fade_out_ms * sample_rate / 1000)
        if fade_out_samples > 0 and fade_out_samples < len(audio_copy):
            fade_out_curve = np.linspace(1, 0, fade_out_samples)
            audio_copy[-fade_out_samples:] *= fade_out_curve
        
        return audio_copy
    
    def add_silence(
        self,
        duration_ms: int,
        sample_rate: int = 24000
    ) -> np.ndarray:
        """
        Generate silence
        
        Args:
            duration_ms: Duration in milliseconds
            sample_rate: Sample rate
            
        Returns:
            Silence as numpy array
        """
        num_samples = int(duration_ms * sample_rate / 1000)
        return np.zeros(num_samples, dtype=np.float32)
    
    def normalize_volume(
        self,
        audio_np: np.ndarray,
        target_level: float = -20.0
    ) -> np.ndarray:
        """
        Normalize audio volume to target level (in dB)
        
        Args:
            audio_np: Input audio
            target_level: Target level in dB
            
        Returns:
            Normalized audio
        """
        # Calculate current RMS
        rms = np.sqrt(np.mean(audio_np ** 2))
        
        if rms == 0:
            return audio_np
        
        # Convert target level from dB to linear
        target_rms = 10 ** (target_level / 20)
        
        # Calculate gain
        gain = target_rms / rms
        
        # Apply gain with clipping protection
        normalized = audio_np * gain
        normalized = np.clip(normalized, -1.0, 1.0)
        
        return normalized

