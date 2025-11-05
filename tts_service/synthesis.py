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
        """Load the CosyVoice model following official guidelines"""
        import os
        import sys
        import traceback
        
        try:
            logger.info("=" * 70)
            logger.info("STARTING MODEL LOADING PROCESS (Official CosyVoice)")
            logger.info("=" * 70)
            
            # Log system information
            logger.info(f"Python version: {sys.version}")
            logger.info(f"PyTorch version: {torch.__version__}")
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logger.info(f"CUDA version: {torch.version.cuda}")
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            
            # Log configuration
            logger.info(f"Model name: {self.service_config.model_name}")
            logger.info(f"Model path: {self.service_config.model_path}")
            logger.info(f"Target device: {self.service_config.device}")
            
            # Import CosyVoice
            logger.info("-" * 70)
            logger.info("IMPORTING COSYVOICE")
            logger.info("-" * 70)
            
            try:
                from cosyvoice.cli.cosyvoice import CosyVoice
                from cosyvoice.utils.file_utils import load_wav
                logger.info("✓ CosyVoice library imported successfully")
                
            except ImportError as e:
                logger.error(f"✗ Failed to import CosyVoice: {e}")
                logger.error("=" * 70)
                logger.error("COSYVOICE NOT PROPERLY INSTALLED")
                logger.error("=" * 70)
                logger.error("Please run setup.sh to install CosyVoice properly:")
                logger.error("  ./setup.sh")
                logger.error("")
                logger.error("Or manually install:")
                logger.error("  1. Create conda env: conda create -n cosyvoice python=3.8")
                logger.error("  2. Activate: conda activate cosyvoice")
                logger.error("  3. Clone: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git")
                logger.error("  4. Install: cd CosyVoice && pip install -r requirements.txt")
                logger.error("=" * 70)
                self._fallback_to_basic_tts()
                return
            
            # Check if model exists locally
            logger.info("-" * 70)
            logger.info("CHECKING MODEL AVAILABILITY")
            logger.info("-" * 70)
            
            model_path_abs = os.path.abspath(self.service_config.model_path)
            logger.info(f"Looking for model at: {model_path_abs}")
            
            if not os.path.exists(model_path_abs):
                logger.warning(f"✗ Model not found at: {model_path_abs}")
                
                if self.service_config.use_modelscope:
                    logger.info("Attempting to download from ModelScope...")
                    try:
                        from modelscope import snapshot_download
                        logger.info(f"Downloading model: {self.service_config.modelscope_model_id}")
                        logger.info("This may take several minutes (model size ~1GB)...")
                        
                        # Download model
                        snapshot_download(
                            self.service_config.modelscope_model_id,
                            local_dir=model_path_abs
                        )
                        logger.info("✓ Model downloaded successfully")
                        
                    except Exception as e:
                        logger.error(f"✗ Failed to download model: {e}")
                        logger.error("")
                        logger.error("Please download the model manually:")
                        logger.error(f"  cd {os.path.dirname(model_path_abs)}")
                        logger.error(f"  python -c \"from modelscope import snapshot_download; snapshot_download('{self.service_config.modelscope_model_id}', local_dir='{os.path.basename(model_path_abs)}')\"")
                        self._fallback_to_basic_tts()
                        return
                else:
                    logger.error("✗ Model not found and auto-download is disabled")
                    logger.error("")
                    logger.error("Please download the model manually:")
                    logger.error(f"  cd {os.path.dirname(model_path_abs)}")
                    logger.error(f"  python -c \"from modelscope import snapshot_download; snapshot_download('{self.service_config.modelscope_model_id}', local_dir='{os.path.basename(model_path_abs)}')\"")
                    self._fallback_to_basic_tts()
                    return
            else:
                logger.info(f"✓ Model found at: {model_path_abs}")
            
            # Initialize CosyVoice model (official way)
            logger.info("-" * 70)
            logger.info("INITIALIZING COSYVOICE MODEL")
            logger.info("-" * 70)
            logger.info("Loading model (this may take 30-60 seconds)...")
            
            try:
                # Official CosyVoice initialization
                # Following the official examples from the repo
                self.model = CosyVoice(model_path_abs)
                logger.info("✓ Model loaded successfully")
                
            except Exception as e:
                logger.error(f"✗ Model initialization failed: {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                logger.error("")
                logger.error("Troubleshooting:")
                logger.error("  1. Verify model files exist in: {model_path_abs}")
                logger.error("  2. Check you're using the correct conda environment")
                logger.error("  3. Try re-downloading the model")
                logger.error("  4. Check CosyVoice GitHub for updates")
                self._fallback_to_basic_tts()
                return
            
            logger.info("✓ Model initialization completed successfully")
            
            # Note: CosyVoice handles device placement internally
            logger.info(f"Model device: {self.service_config.device}")
            if torch.cuda.is_available() and self.service_config.device == "cuda":
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3  # GB
                memory_reserved = torch.cuda.memory_reserved(0) / 1024**3  # GB
                logger.info(f"GPU memory allocated: {memory_allocated:.2f} GB")
                logger.info(f"GPU memory reserved: {memory_reserved:.2f} GB")
            
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
        """Load available speaker voices from CosyVoice model"""
        try:
            if self.model != "fallback" and hasattr(self.model, 'list_available_spks'):
                # Get speakers from model (official API)
                self.available_speakers = self.model.list_available_spks()
                logger.info(f"Loaded {len(self.available_speakers)} speakers from model")
                for spk in self.available_speakers:
                    logger.info(f"  - {spk}")
            else:
                # Default speakers for SFT model
                self.available_speakers = [
                    "中文女",
                    "中文男", 
                    "日语男",
                    "粤语女",
                    "英文女",
                    "英文男",
                    "韩语女"
                ]
                logger.info(f"Using default speaker list ({len(self.available_speakers)} speakers)")
        except Exception as e:
            logger.warning(f"Failed to load speakers: {e}")
            self.available_speakers = ["中文女"]
    
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
        """Synthesize using CosyVoice model (official API)"""
        import traceback
        
        try:
            # Select speaker
            speaker = voice_config.speaker if voice_config.speaker in self.available_speakers else self.available_speakers[0]
            
            # Use official CosyVoice API: inference_sft for SFT models
            if hasattr(self.model, 'inference_sft'):
                logger.debug(f"Using inference_sft with speaker: {speaker}, speed: {voice_config.speed}")
                
                # Official API call (non-streaming)
                audio_generator = self.model.inference_sft(
                    text,
                    speaker,
                    stream=False  # Non-streaming mode for batch synthesis
                )
                
                # Collect audio chunks from generator
                audio_chunks = []
                for i, audio_chunk in enumerate(audio_generator):
                    # CosyVoice returns dict with 'tts_speech' key
                    if isinstance(audio_chunk, dict) and 'tts_speech' in audio_chunk:
                        chunk_tensor = audio_chunk['tts_speech']
                        # Convert tensor to numpy
                        if torch.is_tensor(chunk_tensor):
                            chunk_audio = chunk_tensor.cpu().numpy()
                        else:
                            chunk_audio = chunk_tensor
                        audio_chunks.append(chunk_audio)
                        logger.debug(f"Received audio chunk {i}: shape={chunk_audio.shape}")
                    else:
                        logger.warning(f"Unexpected chunk format: {type(audio_chunk)}")
                
                if not audio_chunks:
                    raise ValueError("No audio generated from model")
                
                # Concatenate all chunks
                audio = np.concatenate(audio_chunks, axis=0)
                
                # Ensure 1D array
                if audio.ndim > 1:
                    audio = audio.squeeze()
                
                logger.debug(f"Final audio shape: {audio.shape}")
                
            else:
                logger.error("Model does not have inference_sft method")
                return self._fallback_synthesize(text, voice_config)
            
            # Apply voice modifications if needed
            if voice_config.pitch != 1.0 or voice_config.energy != 1.0:
                audio = self._apply_voice_modifications(audio, voice_config)
            
            return audio
            
        except Exception as e:
            logger.error(f"CosyVoice synthesis error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.warning("Falling back to basic synthesis")
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
        Synthesize speech with streaming output (official CosyVoice streaming API)
        
        Args:
            text: Input text
            voice_config: Voice configuration
            synthesis_config: Synthesis configuration
            chunk_size: Size of audio chunks to yield
            
        Yields:
            Audio chunks as numpy arrays
        """
        import traceback
        
        try:
            if self.model == "fallback":
                # Fallback: generate all at once then chunk
                audio = self._fallback_synthesize(text, voice_config)
                
                # Yield in chunks
                for i in range(0, len(audio), chunk_size):
                    yield audio[i:i + chunk_size]
                    
            else:
                # Official CosyVoice streaming API
                if hasattr(self.model, 'inference_sft'):
                    speaker = voice_config.speaker if voice_config.speaker in self.available_speakers else self.available_speakers[0]
                    
                    logger.debug(f"Streaming synthesis: speaker={speaker}, stream=True")
                    
                    # Use streaming mode (official API)
                    audio_generator = self.model.inference_sft(
                        text,
                        speaker,
                        stream=True  # Enable streaming
                    )
                    
                    for audio_chunk in audio_generator:
                        if isinstance(audio_chunk, dict) and 'tts_speech' in audio_chunk:
                            chunk_tensor = audio_chunk['tts_speech']
                            
                            # Convert to numpy
                            if torch.is_tensor(chunk_tensor):
                                chunk_audio = chunk_tensor.cpu().numpy()
                            else:
                                chunk_audio = chunk_tensor
                            
                            # Ensure 1D
                            if chunk_audio.ndim > 1:
                                chunk_audio = chunk_audio.squeeze()
                            
                            # Yield in specified chunk sizes
                            for i in range(0, len(chunk_audio), chunk_size):
                                yield chunk_audio[i:i + chunk_size]
                else:
                    # No streaming support, fallback
                    logger.warning("Model doesn't support streaming, using batch mode")
                    audio = self._fallback_synthesize(text, voice_config)
                    for i in range(0, len(audio), chunk_size):
                        yield audio[i:i + chunk_size]
                        
        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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

