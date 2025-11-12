#!/usr/bin/env python3
"""
Audio format conversion with FFmpeg support
Production-ready with all ElevenLabs formats
"""

import struct
import audioop
import io
import wave
import numpy as np
from typing import Optional
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

# Try to import pydub for high-level MP3 encoding
try:
    from pydub import AudioSegment
    HAS_PYDUB = True
    logger.info("✓ pydub available for audio conversion")
except ImportError:
    HAS_PYDUB = False
    logger.warning("⚠ pydub not installed - will use ffmpeg directly")

# Check if ffmpeg is available
def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

HAS_FFMPEG = check_ffmpeg()
if HAS_FFMPEG:
    logger.info("✓ ffmpeg available for audio encoding")
else:
    logger.warning("⚠ ffmpeg not found - MP3/Opus encoding will be limited")
    logger.warning("Install: sudo apt-get install ffmpeg (Linux) or brew install ffmpeg (Mac)")


class AudioFormatConfig:
    """Parse ElevenLabs format string"""
    
    def __init__(self, format_string: str = "mp3_44100_128"):
        parts = format_string.split("_")
        self.codec = parts[0]
        self.sample_rate = int(parts[1]) if len(parts) > 1 else 44100
        self.bitrate = int(parts[2]) if len(parts) > 2 else 128
        
    @property
    def bytes_per_sample(self) -> int:
        """Get bytes per sample based on codec"""
        if self.codec in ["pcm_s16le", "pcm"]:
            return 2
        elif self.codec == "pcm_f32le":
            return 4
        elif self.codec in ["ulaw", "alaw"]:
            return 1
        return 2


class AudioConverter:
    """Handles audio format conversion using FFmpeg"""
    
    def __init__(self, output_format: str = "mp3_44100_128"):
        self.format_config = AudioFormatConfig(output_format)
        # ElevenLabs-style chunk size
        self.streaming_chunk_size = 8192
        
    def numpy_to_pcm16(self, audio_np: np.ndarray) -> bytes:
        """Convert numpy array to 16-bit PCM bytes"""
        audio_np = np.clip(audio_np, -1.0, 1.0)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        return audio_int16.tobytes()
    
    def numpy_to_ulaw(self, audio_np: np.ndarray) -> bytes:
        """Convert numpy array to μ-law"""
        audio_np = np.clip(audio_np, -1.0, 1.0)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        pcm_bytes = audio_int16.tobytes()
        return audioop.lin2ulaw(pcm_bytes, 2)
    
    def numpy_to_alaw(self, audio_np: np.ndarray) -> bytes:
        """Convert numpy array to A-law"""
        audio_np = np.clip(audio_np, -1.0, 1.0)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        pcm_bytes = audio_int16.tobytes()
        return audioop.lin2alaw(pcm_bytes, 2)
    
    def resample(self, audio_bytes: bytes, source_rate: int, target_rate: int) -> bytes:
        """Resample audio using audioop"""
        if source_rate == target_rate:
            return audio_bytes
        
        resampled, _ = audioop.ratecv(
            audio_bytes, 2, 1, source_rate, target_rate, None
        )
        return resampled
    
    def convert_to_mp3_pydub(self, audio_bytes: bytes, sample_rate: int) -> bytes:
        """Convert PCM to MP3 using pydub (preferred method)"""
        try:
            audio_segment = AudioSegment(
                data=audio_bytes,
                sample_width=2,
                frame_rate=sample_rate,
                channels=1
            )
            
            buffer = io.BytesIO()
            audio_segment.export(
                buffer,
                format="mp3",
                bitrate=f"{self.format_config.bitrate}k",
                parameters=["-ar", str(self.format_config.sample_rate)]
            )
            
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"pydub MP3 conversion failed: {e}")
            raise
    
    def convert_to_mp3_ffmpeg(self, audio_bytes: bytes, sample_rate: int) -> bytes:
        """Convert PCM to MP3 using ffmpeg directly"""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as pcm_file:
                pcm_path = pcm_file.name
                pcm_file.write(audio_bytes)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
                mp3_path = mp3_file.name
            
            # FFmpeg command
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-f', 's16le',  # Input format: signed 16-bit little-endian
                '-ar', str(sample_rate),  # Input sample rate
                '-ac', '1',  # Input channels: mono
                '-i', pcm_path,  # Input file
                '-ar', str(self.format_config.sample_rate),  # Output sample rate
                '-b:a', f'{self.format_config.bitrate}k',  # Output bitrate
                '-f', 'mp3',  # Output format
                mp3_path  # Output file
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr.decode()}")
            
            # Read output
            with open(mp3_path, 'rb') as f:
                mp3_data = f.read()
            
            # Cleanup
            os.unlink(pcm_path)
            os.unlink(mp3_path)
            
            return mp3_data
            
        except Exception as e:
            logger.error(f"ffmpeg MP3 conversion failed: {e}")
            # Cleanup on error
            try:
                os.unlink(pcm_path)
                os.unlink(mp3_path)
            except:
                pass
            raise
    
    def convert_to_opus_ffmpeg(self, audio_bytes: bytes, sample_rate: int) -> bytes:
        """Convert PCM to Opus using ffmpeg"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as pcm_file:
                pcm_path = pcm_file.name
                pcm_file.write(audio_bytes)
            
            with tempfile.NamedTemporaryFile(suffix='.opus', delete=False) as opus_file:
                opus_path = opus_file.name
            
            cmd = [
                'ffmpeg',
                '-y',
                '-f', 's16le',
                '-ar', str(sample_rate),
                '-ac', '1',
                '-i', pcm_path,
                '-ar', str(self.format_config.sample_rate),
                '-c:a', 'libopus',
                '-b:a', f'{self.format_config.bitrate}k',
                opus_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg opus failed: {result.stderr.decode()}")
            
            with open(opus_path, 'rb') as f:
                opus_data = f.read()
            
            os.unlink(pcm_path)
            os.unlink(opus_path)
            
            return opus_data
            
        except Exception as e:
            logger.error(f"Opus conversion failed: {e}")
            try:
                os.unlink(pcm_path)
                os.unlink(opus_path)
            except:
                pass
            raise
    
    def convert_audio(self, audio_np: np.ndarray, source_sample_rate: int) -> bytes:
        """
        Convert audio to target format
        
        Supported formats:
        - MP3: using pydub (preferred) or ffmpeg
        - PCM: native conversion
        - μ-law/A-law: native conversion
        - Opus: using ffmpeg
        """
        codec = self.format_config.codec
        target_rate = self.format_config.sample_rate
        
        # Convert to PCM16
        audio_bytes = self.numpy_to_pcm16(audio_np)
        
        # Resample if needed
        if source_sample_rate != target_rate and codec not in ["ulaw", "alaw"]:
            audio_bytes = self.resample(audio_bytes, source_sample_rate, target_rate)
        
        # Encode to target format
        if codec == "mp3":
            # Try pydub first, fallback to ffmpeg
            if HAS_PYDUB:
                try:
                    return self.convert_to_mp3_pydub(audio_bytes, target_rate)
                except Exception as e:
                    logger.warning(f"pydub failed, trying ffmpeg: {e}")
            
            if HAS_FFMPEG:
                return self.convert_to_mp3_ffmpeg(audio_bytes, target_rate)
            else:
                logger.warning("No MP3 encoder available, returning WAV")
                return self._wrap_wav(audio_bytes, target_rate)
        
        elif codec == "pcm":
            return audio_bytes
        
        elif codec == "ulaw":
            # Resample to 8kHz for μ-law
            if target_rate != 8000:
                audio_bytes = self.resample(audio_bytes, target_rate, 8000)
            return self.numpy_to_ulaw(
                np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            )
        
        elif codec == "alaw":
            # Resample to 8kHz for A-law
            if target_rate != 8000:
                audio_bytes = self.resample(audio_bytes, target_rate, 8000)
            return self.numpy_to_alaw(
                np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            )
        
        elif codec == "opus":
            if HAS_FFMPEG:
                return self.convert_to_opus_ffmpeg(audio_bytes, target_rate)
            else:
                logger.warning("ffmpeg not available, returning PCM")
                return audio_bytes
        
        elif codec == "wav":
            return self._wrap_wav(audio_bytes, target_rate)
        
        else:
            logger.warning(f"Unknown codec {codec}, returning PCM")
            return audio_bytes
    
    def _wrap_wav(self, audio_bytes: bytes, sample_rate: int) -> bytes:
        """Wrap PCM in WAV container"""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        return buffer.getvalue()
    
    def chunk_for_streaming(
        self,
        audio_np: np.ndarray,
        source_sample_rate: int
    ) -> list[bytes]:
        """
        Split audio into ElevenLabs-style streaming chunks
        
        Returns larger chunks (8192 samples) for smooth streaming
        """
        # Convert entire audio first
        audio_bytes = self.convert_audio(audio_np, source_sample_rate)
        
        # For compressed formats (MP3, Opus), we can't easily chunk
        # So we return the whole thing as one chunk
        if self.format_config.codec in ["mp3", "opus"]:
            # Split into reasonable chunks for streaming (256KB chunks)
            chunk_size = 256 * 1024
            chunks = []
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                if len(chunk) > 0:
                    chunks.append(chunk)
            return chunks if chunks else [audio_bytes]
        
        # For PCM formats, chunk by sample count
        bytes_per_sample = self.format_config.bytes_per_sample
        chunk_size_bytes = self.streaming_chunk_size * bytes_per_sample
        
        chunks = []
        for i in range(0, len(audio_bytes), chunk_size_bytes):
            chunk = audio_bytes[i:i + chunk_size_bytes]
            if len(chunk) > 0:
                chunks.append(chunk)
        
        return chunks if chunks else [audio_bytes]