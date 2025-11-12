#!/usr/bin/env python3
"""
Audio format conversion and processing utilities
"""

import struct
import audioop
import numpy as np
from typing import Optional, Tuple
import logging
import subprocess
import shutil

from config import AudioConfig

logger = logging.getLogger(__name__)


class AudioConverter:
    """Handles audio format conversion and normalization"""
    
    # Required format for Faster Whisper Large v3
    REQUIRED_SAMPLE_RATE = 16000
    REQUIRED_CHANNELS = 1
    REQUIRED_ENCODING = "pcm_s16le"
    
    def __init__(self, audio_config: AudioConfig):
        self.config = audio_config
        self._ffmpeg_available = None
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        if self._ffmpeg_available is None:
            self._ffmpeg_available = shutil.which("ffmpeg") is not None
            if not self._ffmpeg_available:
                logger.warning("ffmpeg not found. Falling back to basic audio conversion.")
        return self._ffmpeg_available
    
    def _normalize_with_ffmpeg(self, audio_bytes: bytes) -> bytes:
        """
        Normalize audio using ffmpeg to 16kHz PCM mono
        Uses stdin/stdout pipes for low latency
        
        Args:
            audio_bytes: Input audio bytes in any format
            
        Returns:
            Normalized audio (PCM16, mono, 16kHz)
        """
        try:
            # Use ffmpeg to convert to required format
            # -f s16le: 16-bit signed little-endian PCM
            # -ar 16000: 16kHz sample rate
            # -ac 1: mono channel
            # -i pipe:0: read from stdin
            # -f s16le: output format
            # pipe:1: write to stdout
            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-f", "s16le",  # Try to detect format, but assume PCM16 if unknown
                    "-ar", "44100",  # Default sample rate (will be overridden by detection)
                    "-ac", "2",      # Default stereo (will be overridden)
                    "-i", "pipe:0",  # Read from stdin
                    "-f", "s16le",   # Output format: 16-bit PCM
                    "-ar", str(self.REQUIRED_SAMPLE_RATE),  # 16kHz
                    "-ac", str(self.REQUIRED_CHANNELS),     # Mono
                    "-loglevel", "error",  # Suppress ffmpeg output
                    "pipe:1"          # Write to stdout
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=audio_bytes, timeout=10)
            
            if process.returncode != 0:
                # If that failed, try auto-detecting format
                return self._normalize_with_ffmpeg_autodetect(audio_bytes)
            
            return stdout
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg conversion timed out")
            process.kill()
            raise
        except Exception as e:
            logger.warning(f"ffmpeg conversion failed: {e}, trying autodetect")
            return self._normalize_with_ffmpeg_autodetect(audio_bytes)
    
    def _normalize_with_ffmpeg_autodetect(self, audio_bytes: bytes) -> bytes:
        """
        Normalize audio using ffmpeg with format autodetection
        This handles various input formats (mp3, wav, ogg, etc.)
        For raw PCM chunks, tries config-based format first, then autodetect
        """
        # First, try with known format from config (for realtime PCM chunks)
        if self.config.encoding == "pcm_s16le" and len(audio_bytes) > 0:
            try:
                # Try with config format first (faster for realtime chunks)
                process = subprocess.Popen(
                    [
                        "ffmpeg",
                        "-f", "s16le",  # 16-bit PCM
                        "-ar", str(self.config.sample_rate),
                        "-ac", str(self.config.channels),
                        "-i", "pipe:0",
                        "-f", "s16le",
                        "-ar", str(self.REQUIRED_SAMPLE_RATE),
                        "-ac", str(self.REQUIRED_CHANNELS),
                        "-loglevel", "error",
                        "pipe:1"
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(input=audio_bytes, timeout=5)
                
                if process.returncode == 0:
                    return stdout
            except Exception:
                # Fall through to autodetect
                pass
        
        # Try autodetect (for files with headers like mp3, wav, etc.)
        try:
            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-i", "pipe:0",  # Auto-detect input format from stdin
                    "-f", "s16le",   # Output format: 16-bit PCM
                    "-ar", str(self.REQUIRED_SAMPLE_RATE),  # 16kHz
                    "-ac", str(self.REQUIRED_CHANNELS),     # Mono
                    "-loglevel", "error",  # Suppress ffmpeg output
                    "pipe:1"          # Write to stdout
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=audio_bytes, timeout=10)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                logger.error(f"ffmpeg autodetect failed: {error_msg}")
                raise RuntimeError(f"Audio conversion failed: {error_msg}")
            
            return stdout
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg autodetect conversion timed out")
            process.kill()
            raise
        except Exception as e:
            logger.error(f"ffmpeg autodetect conversion error: {e}")
            raise
        
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
        Complete audio normalization pipeline using ffmpeg:
        Always converts to 16kHz PCM mono regardless of input format
        Optimized to skip conversion if format already matches requirements
        
        Args:
            audio_bytes: Input audio in any format
            
        Returns:
            Normalized audio (PCM16, mono, 16kHz)
        """
        # Quick check: if config already matches requirements, verify with ffmpeg
        # but use fast path for realtime streaming
        if (self.config.encoding == self.REQUIRED_ENCODING and
            self.config.sample_rate == self.REQUIRED_SAMPLE_RATE and
            self.config.channels == self.REQUIRED_CHANNELS):
            # Format matches requirements - still use ffmpeg to verify and handle edge cases
            # but with optimized parameters
            if self._check_ffmpeg():
                try:
                    # Fast path: same format, just verify and passthrough
                    process = subprocess.Popen(
                        [
                            "ffmpeg",
                            "-f", "s16le",
                            "-ar", str(self.REQUIRED_SAMPLE_RATE),
                            "-ac", str(self.REQUIRED_CHANNELS),
                            "-i", "pipe:0",
                            "-f", "s16le",
                            "-ar", str(self.REQUIRED_SAMPLE_RATE),
                            "-ac", str(self.REQUIRED_CHANNELS),
                            "-loglevel", "error",
                            "pipe:1"
                        ],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    stdout, stderr = process.communicate(input=audio_bytes, timeout=2)
                    if process.returncode == 0:
                        return stdout
                except Exception:
                    # Fall through to full normalization
                    pass
        
        # Use ffmpeg if available for robust format handling
        if self._check_ffmpeg():
            try:
                return self._normalize_with_ffmpeg_autodetect(audio_bytes)
            except Exception as e:
                logger.warning(f"ffmpeg normalization failed: {e}, falling back to basic conversion")
                # Fall through to basic conversion
        
        # Fallback to basic conversion if ffmpeg fails or unavailable
        # This assumes the audio is already in a known format from config
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

