#!/usr/bin/env python3
"""
Voice Activity Detection (VAD) processor
"""

from collections import deque
from typing import Dict, Any, Optional
import logging

import webrtcvad

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
    """Manages audio buffering and VAD for streaming"""
    
    def __init__(self, vad_config: VADConfig, audio_config: AudioConfig):
        self.vad_config = vad_config
        self.audio_config = audio_config
        
        # Calculate frame size based on sample rate and frame duration
        # Frame size in samples
        samples_per_frame = int(
            audio_config.sample_rate * vad_config.frame_duration / 1000
        )
        # Frame size in bytes (16-bit = 2 bytes per sample, mono)
        self.frame_size = samples_per_frame * 2
        
        # Initialize VAD
        self.vad = None
        if vad_config.enabled:
            try:
                self.vad = webrtcvad.Vad(vad_config.mode)
                logger.info(f"VAD initialized (mode={vad_config.mode}, frame_duration={vad_config.frame_duration}ms)")
            except Exception as e:
                logger.error(f"Failed to initialize VAD: {e}")
                self.vad_config.enabled = False
        
        # Buffers
        self.buffer = bytearray()
        self.speech_buffer = bytearray()
        
        # State tracking
        self.speech_frames = deque(maxlen=100)
        self.silence_frames = 0
        self.is_speaking = False
        self.total_speech_frames = 0
        
    def add_audio(self, audio_bytes: bytes) -> VADResult:
        """
        Add audio bytes and perform VAD processing
        
        Args:
            audio_bytes: Audio bytes (must be PCM16, mono, 16kHz)
            
        Returns:
            VADResult with detection information
        """
        if not self.vad_config.enabled:
            # VAD disabled, just accumulate audio
            return self._no_vad_mode(audio_bytes)
        
        self.buffer.extend(audio_bytes)
        
        result = VADResult()
        
        # Process complete frames
        while len(self.buffer) >= self.frame_size:
            frame = bytes(self.buffer[:self.frame_size])
            self.buffer = self.buffer[self.frame_size:]
            
            # Run VAD on frame
            vad_result = self._process_frame(frame)
            
            if vad_result:
                result = vad_result
                if result.end_of_utterance:
                    break
        
        return result
    
    def _process_frame(self, frame: bytes) -> Optional[VADResult]:
        """Process a single audio frame with VAD"""
        try:
            is_speech = self.vad.is_speech(frame, self.audio_config.sample_rate)
            
            self.speech_frames.append(is_speech)
            
            if is_speech:
                return self._handle_speech_frame(frame)
            else:
                return self._handle_silence_frame(frame)
                
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
            return None
    
    def _handle_speech_frame(self, frame: bytes) -> VADResult:
        """Handle a frame detected as speech"""
        self.silence_frames = 0
        self.total_speech_frames += 1
        
        # Start speaking if not already
        if not self.is_speaking:
            speech_ratio = sum(self.speech_frames) / len(self.speech_frames)
            if speech_ratio >= self.vad_config.speech_threshold:
                self.is_speaking = True
                self.speech_buffer = bytearray()
                logger.debug("Speech started")
        
        # Accumulate audio
        if self.is_speaking:
            self.speech_buffer.extend(frame)
        
        return VADResult(
            has_speech=True,
            is_speaking=self.is_speaking,
            speech_duration=self._get_speech_duration()
        )
    
    def _handle_silence_frame(self, frame: bytes) -> VADResult:
        """Handle a frame detected as silence"""
        result = VADResult()
        
        if self.is_speaking:
            self.silence_frames += 1
            self.speech_buffer.extend(frame)
            
            silence_duration = self._get_silence_duration()
            speech_duration = self._get_speech_duration()
            
            result.is_speaking = True
            result.speech_duration = speech_duration
            result.silence_duration = silence_duration
            
            # Check for end of utterance
            if (silence_duration >= self.vad_config.silence_duration and
                speech_duration >= self.vad_config.min_speech_duration):
                
                result.end_of_utterance = True
                result.audio_for_transcription = bytes(self.speech_buffer)
                
                logger.debug(
                    f"End of utterance (speech={speech_duration:.2f}s, "
                    f"silence={silence_duration:.2f}s)"
                )
                
                # Reset state
                self._reset_state()
        
        return result
    
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
        
        if speech_duration >= self.vad_config.min_speech_duration:
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
        self.speech_frames.clear()
        self.silence_frames = 0
        self.is_speaking = False
        self.total_speech_frames = 0
    
    def _get_speech_duration(self) -> float:
        """Calculate current speech duration in seconds"""
        if len(self.speech_buffer) == 0:
            return 0.0
        return len(self.speech_buffer) / (self.audio_config.sample_rate * 2)
    
    def _get_silence_duration(self) -> float:
        """Calculate current silence duration in seconds"""
        return (self.silence_frames * self.vad_config.frame_duration) / 1000.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current buffer statistics"""
        return {
            "is_speaking": self.is_speaking,
            "speech_duration": self._get_speech_duration(),
            "silence_duration": self._get_silence_duration(),
            "buffer_size": len(self.speech_buffer),
            "frame_buffer_size": len(self.buffer),
            "total_speech_frames": self.total_speech_frames
        }

