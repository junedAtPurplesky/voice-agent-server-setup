#!/usr/bin/env python3
"""
Voice Activity Detection (VAD) processor using Silero VAD
"""

from collections import deque
from typing import Dict, Any, Optional
import logging
import numpy as np
import torch

from config import VADConfig, AudioConfig

logger = logging.getLogger(__name__)


class VADResult:
    """Result of VAD processing"""
    def __init__(
        self,
        has_speech: bool = False,
        end_of_utterance: bool = False,
        audio_for_transcription: Optional[bytes] = None,
        is_speaking: bool = False,
        speech_duration: float = 0.0,
        silence_duration: float = 0.0
    ):
        self.has_speech = has_speech
        self.end_of_utterance = end_of_utterance
        self.audio_for_transcription = audio_for_transcription
        self.is_speaking = is_speaking
        self.speech_duration = speech_duration
        self.silence_duration = silence_duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "has_speech": self.has_speech,
            "end_of_utterance": self.end_of_utterance,
            "is_speaking": self.is_speaking,
            "speech_duration": self.speech_duration,
            "silence_duration": self.silence_duration
        }


class AudioBuffer:
    """Manages audio buffering and VAD for streaming using Silero VAD"""
    
    def __init__(self, vad_config: VADConfig, audio_config: AudioConfig):
        self.vad_config = vad_config
        self.audio_config = audio_config
        
        # Initialize Silero VAD
        self.vad_model = None
        self.get_speech_timestamps = None
        self.read_audio = None
        
        if vad_config.enabled:
            try:
                self._load_silero_vad()
                logger.info("Silero VAD initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Silero VAD: {e}")
                self.vad_config.enabled = False
        
        # Buffers
        self.buffer = bytearray()
        self.speech_buffer = bytearray()
        
        # State tracking
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.silence_start_time = None
        
    def _load_silero_vad(self):
        """Load Silero VAD model"""
        try:
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.vad_model = model
            (self.get_speech_timestamps, _, self.read_audio, _, _) = utils
            logger.info("Silero VAD model loaded")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise
    
    def add_audio(self, audio_bytes: bytes) -> VADResult:
        """
        Add audio bytes and perform VAD processing
        
        Args:
            audio_bytes: Audio bytes (must be PCM16, mono, 16kHz)
            
        Returns:
            VADResult with detection information
        """
        if not self.vad_config.enabled:
            return self._no_vad_mode(audio_bytes)
        
        # Add to buffer
        self.buffer.extend(audio_bytes)
        self.speech_buffer.extend(audio_bytes)
        
        # Process in chunks (Silero VAD works best with larger chunks)
        # Process when we have at least 0.5 seconds of audio (8000 samples * 2 bytes = 16000 bytes)
        min_chunk_size = self.vad_config.sample_rate * 1  # 0.5 second in bytes
        max_buffer_size = self.vad_config.sample_rate * 2 * 2  # 2 seconds
        
        result = VADResult()
        
        if len(self.buffer) >= min_chunk_size:
            # Convert buffer to numpy array
            audio_np = self._bytes_to_numpy(bytes(self.buffer))
            
            # Run VAD
            try:
                speech_timestamps = self.get_speech_timestamps(
                    audio_np,
                    self.vad_model,
                    threshold=self.vad_config.threshold,
                    min_speech_duration_ms=self.vad_config.min_speech_duration_ms,
                    min_silence_duration_ms=self.vad_config.min_silence_duration_ms,
                    speech_pad_ms=self.vad_config.speech_pad_ms,
                    sampling_rate=self.vad_config.sample_rate
                )
                
                # Check if there's speech in the recent audio
                current_time = len(self.buffer) / (self.vad_config.sample_rate * 2)
                recent_speech = False
                
                if speech_timestamps:
                    # Check if there's speech in the last 0.3 seconds
                    for ts in speech_timestamps:
                        if ts['end'] >= current_time - 0.3:
                            recent_speech = True
                            break
                
                if recent_speech:
                    # Speech detected
                    if not self.is_speaking:
                        self.is_speaking = True
                        self.speech_start_time = current_time
                        self.speech_buffer = bytearray(bytes(self.buffer))
                        logger.debug("Speech started")
                    
                    self.last_speech_time = current_time
                    self.silence_start_time = None
                    
                    result.has_speech = True
                    result.is_speaking = True
                    result.speech_duration = self._get_speech_duration()
                    
                    # Keep a rolling buffer (keep last 2 seconds)
                    if len(self.buffer) > max_buffer_size:
                        # Keep only the last 2 seconds
                        self.buffer = bytearray(self.buffer[-max_buffer_size:])
                else:
                    # No recent speech
                    if self.is_speaking:
                        # We were speaking, check for end of utterance
                        if self.silence_start_time is None:
                            self.silence_start_time = current_time
                        
                        silence_duration = current_time - self.silence_start_time
                        speech_duration = self._get_speech_duration()
                        
                        result.is_speaking = True
                        result.speech_duration = speech_duration
                        result.silence_duration = silence_duration
                        
                        # Check if silence is long enough
                        silence_duration_ms = silence_duration * 1000
                        if (silence_duration_ms >= self.vad_config.min_silence_duration_ms and
                            speech_duration >= (self.vad_config.min_speech_duration_ms / 1000.0)):
                            
                            result.end_of_utterance = True
                            result.audio_for_transcription = bytes(self.speech_buffer)
                            
                            logger.debug(
                                f"End of utterance (speech={speech_duration:.2f}s, "
                                f"silence={silence_duration:.2f}s)"
                            )
                            
                            # Reset state
                            self._reset_state()
                    else:
                        # No speech, clear buffer periodically
                        if len(self.buffer) > max_buffer_size:
                            self.buffer.clear()
                            
            except Exception as e:
                logger.error(f"VAD processing error: {e}")
                # Fallback: assume speech if we have audio
                result.has_speech = True
                result.is_speaking = True
        
        return result
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_np = audio_np.astype(np.float32) / 32768.0
        return audio_np
    
    def _no_vad_mode(self, audio_bytes: bytes) -> VADResult:
        """Handle audio when VAD is disabled"""
        self.speech_buffer.extend(audio_bytes)
        
        return VADResult(
            has_speech=True,
            is_speaking=True,
            speech_duration=self._get_speech_duration()
        )
    
    def get_accumulated_audio(self) -> Optional[bytes]:
        """
        Get accumulated speech buffer for partial transcription
        
        Returns:
            Audio bytes if enough speech accumulated, None otherwise
        """
        if len(self.speech_buffer) == 0:
            return None
            
        speech_duration = self._get_speech_duration()
        min_duration = self.vad_config.min_speech_duration_ms / 1000.0
        
        if speech_duration >= min_duration:
            return bytes(self.speech_buffer)
            
        return None
    
    def force_end_utterance(self) -> Optional[bytes]:
        """
        Force end of current utterance and return audio
        
        Returns:
            Audio bytes if any accumulated, None otherwise
        """
        if len(self.speech_buffer) > 0:
            audio = bytes(self.speech_buffer)
            self._reset_state()
            return audio
        return None
    
    def reset(self):
        """Reset all buffers and state"""
        self.buffer.clear()
        self._reset_state()
        logger.debug("Audio buffer reset")
    
    def _reset_state(self):
        """Reset speech detection state"""
        self.speech_buffer.clear()
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.silence_start_time = None
    
    def _get_speech_duration(self) -> float:
        """Calculate current speech duration in seconds"""
        if len(self.speech_buffer) == 0:
            return 0.0
        return len(self.speech_buffer) / (self.audio_config.sample_rate * 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current buffer statistics"""
        return {
            "is_speaking": self.is_speaking,
            "speech_duration": self._get_speech_duration(),
            "silence_duration": (self.silence_start_time - self.last_speech_time) if (self.silence_start_time and self.last_speech_time) else 0.0,
            "buffer_size": len(self.speech_buffer),
            "frame_buffer_size": len(self.buffer)
        }
