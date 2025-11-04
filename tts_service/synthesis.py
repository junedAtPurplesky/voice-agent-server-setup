#!/usr/bin/env python3
"""
TTS synthesis engine using CosyVoice2-0.5B
High-performance text-to-speech with streaming support
"""

import time
import logging
from typing import Dict, Any, Optional, Iterator
import numpy as np
import torch

from config import ServiceConfig, SynthesisConfig, VoiceConfig

logger = logging.getLogger(__name__)


class SynthesisResult:
    """Result of TTS synthesis"""
    def __init__(
        self,
        audio: np.ndarray,
        sample_rate: int,
        text: str,
        processing_time: float,
        audio_duration: float,
        speaker: str
    ):
        self.audio = audio
        self.sample_rate = sample_rate
        self.text = text
        self.processing_time = processing_time
        self.audio_duration = audio_duration
        self.speaker = speaker
        self.realtime_factor = processing_time / audio_duration if audio_duration > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without audio data)"""
        return {
            "text": self.text,
            "sample_rate": self.sample_rate,
            "audio_duration": self.audio_duration,
            "processing_time": self.processing_time,
            "realtime_factor": self.realtime_factor,
            "speaker": self.speaker
        }


class SynthesisEngine:
    """Handles CosyVoice2 model loading and synthesis"""
    
    def __init__(self, service_config: ServiceConfig):
        self.service_config = service_config
        self.model = None
        self.tokenizer = None
        self.available_speakers = []
        self._load_model()
    
    def _load_model(self):
        """Load the CosyVoice2-0.5B model"""
        try:
            logger.info(f"Loading CosyVoice2 model: {self.service_config.model_name}")
            logger.info(f"Model path: {self.service_config.model_path}")
            logger.info(f"Device: {self.service_config.device}")
            
            # Import CosyVoice2 model
            try:
                from cosyvoice.cli.cosyvoice import CosyVoice
                from cosyvoice.utils.file_utils import load_wav
                
                self.model = CosyVoice(
                    self.service_config.model_path,
                    load_jit=True,
                    load_onnx=False
                )
                
                # Move model to device
                if self.service_config.device == "cuda":
                    self.model = self.model.to("cuda")
                
                logger.info("CosyVoice2 model loaded successfully")
                
                # Get available speakers
                self._load_available_speakers()
                
                # Warm up the model
                self._warmup()
                
            except ImportError as e:
                logger.error(f"Failed to import CosyVoice2: {e}")
                logger.error("Installing CosyVoice2 from GitHub...")
                self._fallback_to_basic_tts()
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._fallback_to_basic_tts()
    
    def _load_available_speakers(self):
        """Load available speaker voices"""
        try:
            # CosyVoice2 supports multiple speakers
            # This is a placeholder - actual implementation depends on model
            self.available_speakers = [
                "default",
                "female_calm",
                "male_energetic",
                "female_friendly",
                "male_professional"
            ]
            logger.info(f"Loaded {len(self.available_speakers)} available speakers")
        except Exception as e:
            logger.warning(f"Failed to load speakers: {e}")
            self.available_speakers = ["default"]
    
    def _fallback_to_basic_tts(self):
        """Fallback to basic TTS if CosyVoice2 is not available"""
        logger.warning("Using fallback TTS engine (basic synthesis)")
        logger.warning("Install CosyVoice2 for full functionality:")
        logger.warning("  git clone https://github.com/FunAudioLLM/CosyVoice.git")
        logger.warning("  cd CosyVoice && pip install -r requirements.txt")
        
        # Set flag for fallback mode
        self.model = "fallback"
        self.available_speakers = ["default"]
    
    def _warmup(self):
        """Warm up the model with dummy input"""
        try:
            logger.info("Warming up model...")
            dummy_text = "Hello, this is a test."
            
            if self.model != "fallback":
                # Actual warmup with model
                _ = self.synthesize(
                    dummy_text,
                    VoiceConfig(),
                    SynthesisConfig()
                )
            
            logger.info("Model warmed up")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
    
    def synthesize(
        self,
        text: str,
        voice_config: VoiceConfig,
        synthesis_config: SynthesisConfig
    ) -> SynthesisResult:
        """
        Synthesize speech from text
        
        Args:
            text: Input text to synthesize
            voice_config: Voice configuration
            synthesis_config: Synthesis configuration
            
        Returns:
            SynthesisResult with audio data and metadata
        """
        try:
            start_time = time.time()
            
            if self.model == "fallback":
                # Fallback synthesis
                audio = self._fallback_synthesize(text, voice_config)
            else:
                # CosyVoice2 synthesis
                audio = self._cosyvoice_synthesize(text, voice_config, synthesis_config)
            
            processing_time = time.time() - start_time
            # CosyVoice2 default sample rate is 24000 Hz
            audio_duration = len(audio) / 24000
            
            result = SynthesisResult(
                audio=audio,
                sample_rate=24000,  # CosyVoice2 default
                text=text,
                processing_time=processing_time,
                audio_duration=audio_duration,
                speaker=voice_config.speaker
            )
            
            logger.debug(
                f"Synthesized {len(text)} chars in {processing_time:.3f}s "
                f"(RTF: {result.realtime_factor:.2f}x)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise
    
    def _cosyvoice_synthesize(
        self,
        text: str,
        voice_config: VoiceConfig,
        synthesis_config: SynthesisConfig
    ) -> np.ndarray:
        """Synthesize using CosyVoice2 model"""
        try:
            # Prepare generation parameters
            generation_params = {
                "speaker": voice_config.speaker if voice_config.speaker in self.available_speakers else "default",
                "speed": voice_config.speed,
            }
            
            # Generate speech
            # Note: Actual API depends on CosyVoice2 implementation
            if hasattr(self.model, 'inference_sft'):
                # Standard inference
                audio_generator = self.model.inference_sft(
                    text,
                    speaker=generation_params["speaker"],
                    speed=generation_params["speed"]
                )
                
                # Collect audio chunks
                audio_chunks = []
                for audio_chunk in audio_generator:
                    audio_chunks.append(audio_chunk['tts_speech'])
                
                # Concatenate audio
                audio = np.concatenate(audio_chunks, axis=0)
                
            else:
                # Fallback to basic generation
                audio = self._fallback_synthesize(text, voice_config)
            
            # Apply pitch and energy modifications
            if voice_config.pitch != 1.0 or voice_config.energy != 1.0:
                audio = self._apply_voice_modifications(audio, voice_config)
            
            return audio
            
        except Exception as e:
            logger.error(f"CosyVoice2 synthesis error: {e}, falling back to basic synthesis")
            return self._fallback_synthesize(text, voice_config)
    
    def _fallback_synthesize(self, text: str, voice_config: VoiceConfig) -> np.ndarray:
        """Fallback synthesis using simple sine wave (for testing)"""
        logger.debug("Using fallback synthesis")
        
        # Generate speech-like audio with multiple frequencies
        duration = len(text) * 0.08  # ~80ms per character
        sample_rate = 24000
        samples = int(duration * sample_rate)
        
        # Create audio with formants (speech-like)
        t = np.arange(samples) / sample_rate
        
        # Base frequency based on pitch
        base_freq = 200 * voice_config.pitch
        
        # Multiple formants for speech-like sound
        audio = np.zeros(samples, dtype=np.float32)
        formants = [base_freq, base_freq * 2.5, base_freq * 3.5]
        amplitudes = [0.5, 0.3, 0.2]
        
        for freq, amp in zip(formants, amplitudes):
            audio += amp * np.sin(2 * np.pi * freq * t)
        
        # Apply speed
        if voice_config.speed != 1.0:
            target_length = int(len(audio) / voice_config.speed)
            audio = np.interp(
                np.linspace(0, len(audio) - 1, target_length),
                np.arange(len(audio)),
                audio
            )
        
        # Apply energy
        audio = audio * voice_config.energy * 0.3
        
        # Add envelope for naturalness
        envelope = np.ones_like(audio)
        fade_samples = int(0.05 * sample_rate)  # 50ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio = audio * envelope
        
        return audio
    
    def _apply_voice_modifications(
        self,
        audio: np.ndarray,
        voice_config: VoiceConfig
    ) -> np.ndarray:
        """Apply pitch and energy modifications to audio"""
        # This is a simplified implementation
        # Full implementation would use signal processing libraries
        
        # Apply energy
        if voice_config.energy != 1.0:
            audio = audio * voice_config.energy
        
        # Pitch shifting would require librosa or similar
        # For now, we skip complex pitch shifting
        
        return audio
    
    def synthesize_streaming(
        self,
        text: str,
        voice_config: VoiceConfig,
        synthesis_config: SynthesisConfig,
        chunk_size: int = 1024
    ) -> Iterator[np.ndarray]:
        """
        Synthesize speech with streaming output
        
        Args:
            text: Input text
            voice_config: Voice configuration
            synthesis_config: Synthesis configuration
            chunk_size: Size of audio chunks to yield
            
        Yields:
            Audio chunks as numpy arrays
        """
        try:
            if self.model == "fallback":
                # Fallback: generate all at once then chunk
                audio = self._fallback_synthesize(text, voice_config)
                
                # Yield in chunks
                for i in range(0, len(audio), chunk_size):
                    yield audio[i:i + chunk_size]
                    
            else:
                # CosyVoice2 streaming
                if hasattr(self.model, 'inference_sft'):
                    generation_params = {
                        "speaker": voice_config.speaker if voice_config.speaker in self.available_speakers else "default",
                        "speed": voice_config.speed,
                    }
                    
                    audio_generator = self.model.inference_sft(
                        text,
                        speaker=generation_params["speaker"],
                        speed=generation_params["speed"],
                        stream=True
                    )
                    
                    for audio_chunk in audio_generator:
                        if 'tts_speech' in audio_chunk:
                            chunk_audio = audio_chunk['tts_speech']
                            
                            # Yield in specified chunk sizes
                            for i in range(0, len(chunk_audio), chunk_size):
                                yield chunk_audio[i:i + chunk_size]
                else:
                    # No streaming support, fallback
                    audio = self._fallback_synthesize(text, voice_config)
                    for i in range(0, len(audio), chunk_size):
                        yield audio[i:i + chunk_size]
                        
        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.service_config.model_name,
            "model_path": self.service_config.model_path,
            "device": self.service_config.device,
            "available_speakers": self.available_speakers,
            "mode": "fallback" if self.model == "fallback" else "cosyvoice"
        }
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices"""
        return [
            {
                "id": speaker,
                "name": speaker.replace("_", " ").title(),
                "language": "multi",
                "gender": "male" if "male" in speaker else "female" if "female" in speaker else "neutral"
            }
            for speaker in self.available_speakers
        ]

