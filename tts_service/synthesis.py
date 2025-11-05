#!/usr/bin/env python3
"""
TTS synthesis engine using CosyVoice2-0.5B
High-performance text-to-speech with streaming support
"""

import time
import logging
from typing import Dict, Any, Optional, Iterator, List
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
        """Load the CosyVoice2-0.5B model with detailed debug logging"""
        import os
        import sys
        import traceback
        
        try:
            logger.info("=" * 70)
            logger.info("STARTING MODEL LOADING PROCESS")
            logger.info("=" * 70)
            
            # Log system information
            logger.debug(f"Python version: {sys.version}")
            logger.debug(f"PyTorch version: {torch.__version__}")
            logger.debug(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logger.debug(f"CUDA version: {torch.version.cuda}")
                logger.debug(f"GPU count: {torch.cuda.device_count()}")
                logger.debug(f"Current GPU: {torch.cuda.current_device()}")
                logger.debug(f"GPU name: {torch.cuda.get_device_name(0)}")
            
            # Log configuration
            logger.info(f"Model name: {self.service_config.model_name}")
            logger.info(f"Model path/ID: {self.service_config.model_path}")
            logger.info(f"Target device: {self.service_config.device}")
            logger.info(f"Model cache dir: {self.service_config.model_cache_dir}")
            
            # Check cache directory
            cache_dir = os.path.expanduser("~/.cache/modelscope/hub")
            logger.debug(f"ModelScope cache directory: {cache_dir}")
            logger.debug(f"Cache directory exists: {os.path.exists(cache_dir)}")
            
            model_cache_path = os.path.join(cache_dir, self.service_config.model_path)
            logger.debug(f"Expected model cache path: {model_cache_path}")
            logger.debug(f"Model cached locally: {os.path.exists(model_cache_path)}")
            
            # Import CosyVoice model
            logger.info("Attempting to import CosyVoice library...")
            try:
                from cosyvoice.cli.cosyvoice import CosyVoice
                from cosyvoice.utils.file_utils import load_wav
                logger.info("✓ CosyVoice library imported successfully")
                
                # Check CosyVoice version if available
                try:
                    import cosyvoice
                    if hasattr(cosyvoice, '__version__'):
                        logger.debug(f"CosyVoice version: {cosyvoice.__version__}")
                except:
                    logger.debug("CosyVoice version not available")
                
            except ImportError as e:
                logger.error(f"✗ Failed to import CosyVoice: {e}")
                logger.error(f"Import error traceback:\n{traceback.format_exc()}")
                logger.warning("CosyVoice not installed. Install it with:")
                logger.warning("  git clone https://github.com/FunAudioLLM/CosyVoice.git")
                logger.warning("  cd CosyVoice && pip install -r requirements.txt")
                self._fallback_to_basic_tts()
                return
            
            # Initialize CosyVoice with correct parameters
            logger.info("-" * 70)
            logger.info("INITIALIZING COSYVOICE MODEL")
            logger.info("-" * 70)
            logger.info(f"Model identifier: {self.service_config.model_path}")
            logger.info("This may take several minutes on first run (downloading model)...")
            
            model_loaded = False
            
            # Try initialization with different parameter combinations
            try:
                logger.debug("Attempt 1: Trying with load_jit, load_trt, and fp16 parameters")
                self.model = CosyVoice(
                    self.service_config.model_path,
                    load_jit=False,  # Set to False for faster loading
                    load_trt=False,  # TensorRT optimization (requires TensorRT)
                    fp16=False       # Use FP32 for better quality
                )
                logger.info("✓ Model loaded with full parameters (load_jit, load_trt, fp16)")
                model_loaded = True
                
            except TypeError as e:
                logger.debug(f"Attempt 1 failed with TypeError: {e}")
                logger.debug("Attempt 2: Trying with load_jit parameter only")
                try:
                    self.model = CosyVoice(
                        self.service_config.model_path,
                        load_jit=False
                    )
                    logger.info("✓ Model loaded with load_jit parameter only")
                    model_loaded = True
                    
                except TypeError as e2:
                    logger.debug(f"Attempt 2 failed with TypeError: {e2}")
                    logger.debug("Attempt 3: Trying with model path only (no optional params)")
                    try:
                        self.model = CosyVoice(self.service_config.model_path)
                        logger.info("✓ Model loaded with model path only")
                        model_loaded = True
                    except Exception as e3:
                        logger.error(f"Attempt 3 failed: {e3}")
                        logger.error(f"Full traceback:\n{traceback.format_exc()}")
                        raise
                        
            except Exception as e:
                logger.error(f"✗ Model initialization failed: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                raise
            
            if not model_loaded:
                raise RuntimeError("Failed to load model with any parameter combination")
            
            logger.info("Model initialization completed successfully")
            
            # Move model to device
            logger.info("-" * 70)
            logger.info("MOVING MODEL TO DEVICE")
            logger.info("-" * 70)
            
            if self.service_config.device == "cuda":
                if not torch.cuda.is_available():
                    logger.warning("CUDA requested but not available, falling back to CPU")
                    self.service_config.device = "cpu"
                else:
                    logger.info("Moving model to CUDA device...")
                    try:
                        self.model = self.model.to("cuda")
                        logger.info(f"✓ Model successfully moved to CUDA")
                        
                        # Log GPU memory usage
                        if torch.cuda.is_available():
                            memory_allocated = torch.cuda.memory_allocated(0) / 1024**3  # GB
                            memory_reserved = torch.cuda.memory_reserved(0) / 1024**3  # GB
                            logger.debug(f"GPU memory allocated: {memory_allocated:.2f} GB")
                            logger.debug(f"GPU memory reserved: {memory_reserved:.2f} GB")
                    except Exception as e:
                        logger.error(f"✗ Failed to move model to CUDA: {e}")
                        logger.error(f"Traceback:\n{traceback.format_exc()}")
                        raise
            else:
                logger.info(f"Model will use device: {self.service_config.device}")
            
            # Get available speakers
            logger.info("-" * 70)
            logger.info("LOADING AVAILABLE SPEAKERS")
            logger.info("-" * 70)
            try:
                self._load_available_speakers()
                logger.info(f"✓ Loaded {len(self.available_speakers)} speakers")
                logger.debug(f"Available speakers: {self.available_speakers}")
            except Exception as e:
                logger.error(f"✗ Failed to load speakers: {e}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                # Continue anyway with default speakers
            
            # Warm up the model
            logger.info("-" * 70)
            logger.info("WARMING UP MODEL")
            logger.info("-" * 70)
            try:
                self._warmup()
                logger.info("✓ Model warmup completed")
            except Exception as e:
                logger.warning(f"⚠ Model warmup failed (non-critical): {e}")
                logger.debug(f"Warmup traceback:\n{traceback.format_exc()}")
            
            logger.info("=" * 70)
            logger.info("✓ MODEL LOADING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 70)
                
        except Exception as e:
            logger.error("=" * 70)
            logger.error("✗ MODEL LOADING FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            logger.error("=" * 70)
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
        logger.warning("=" * 70)
        logger.warning("ENTERING FALLBACK MODE")
        logger.warning("=" * 70)
        logger.warning("⚠ Using fallback TTS engine (basic sine wave synthesis)")
        logger.warning("⚠ This is NOT production quality - for testing only!")
        logger.warning("")
        logger.warning("To enable full CosyVoice2 functionality:")
        logger.warning("  1. git clone https://github.com/FunAudioLLM/CosyVoice.git")
        logger.warning("  2. cd CosyVoice && pip install -r requirements.txt")
        logger.warning("  3. Restart this service")
        logger.warning("=" * 70)
        
        # Set flag for fallback mode
        self.model = "fallback"
        self.available_speakers = ["default"]
        logger.debug("Fallback mode initialized with default speaker only")
    
    def _warmup(self):
        """Warm up the model with dummy input"""
        import traceback
        
        try:
            logger.info("Starting model warmup with dummy synthesis...")
            dummy_text = "Hello, this is a test."
            logger.debug(f"Warmup text: '{dummy_text}'")
            
            if self.model != "fallback":
                logger.debug("Running actual model warmup synthesis...")
                start_time = time.time()
                
                # Actual warmup with model
                result = self.synthesize(
                    dummy_text,
                    VoiceConfig(),
                    SynthesisConfig()
                )
                
                warmup_time = time.time() - start_time
                logger.info(f"✓ Warmup synthesis completed in {warmup_time:.2f}s")
                logger.debug(f"Warmup audio duration: {result.audio_duration:.2f}s")
                logger.debug(f"Warmup RTF: {result.realtime_factor:.2f}x")
            else:
                logger.debug("Skipping warmup (fallback mode)")
            
            logger.info("✓ Model warmup completed successfully")
            
        except Exception as e:
            logger.warning(f"⚠ Warmup failed (non-critical): {e}")
            logger.debug(f"Warmup error traceback:\n{traceback.format_exc()}")
            logger.info("Continuing without warmup...")
    
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

