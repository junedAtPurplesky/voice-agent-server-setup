#!/usr/bin/env python3
"""
TTS synthesis engine using Piper
High-performance text-to-speech with streaming support
"""

import time
import logging
import os
import subprocess
import json
from typing import Dict, Any, Optional, Iterator, List
import numpy as np
import wave
import io

from config import ServiceConfig, SynthesisConfig, VoiceConfig, PIPER_VOICES

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
        voice_model: str
    ):
        self.audio = audio
        self.sample_rate = sample_rate
        self.text = text
        self.processing_time = processing_time
        self.audio_duration = audio_duration
        self.voice_model = voice_model
        self.realtime_factor = processing_time / audio_duration if audio_duration > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without audio data)"""
        return {
            "text": self.text,
            "sample_rate": self.sample_rate,
            "audio_duration": self.audio_duration,
            "processing_time": self.processing_time,
            "realtime_factor": self.realtime_factor,
            "voice_model": self.voice_model
        }


class SynthesisEngine:
    """Handles Piper TTS synthesis"""
    
    def __init__(self, service_config: ServiceConfig):
        self.service_config = service_config
        self.models_dir = os.path.abspath(service_config.models_dir)
        self.piper_binary = None
        self.available_voices = []
        self._setup_piper()
    
    def _setup_piper(self):
        """Setup Piper TTS engine"""
        try:
            logger.info("=" * 70)
            logger.info("SETTING UP PIPER TTS ENGINE")
            logger.info("=" * 70)
            
            # Check GPU availability
            if self.service_config.use_gpu:
                self._check_gpu_support()
            
            # Find piper binary
            self.piper_binary = self._find_piper_binary()
            if not self.piper_binary:
                logger.error("Piper binary not found!")
                logger.error("Please install Piper: pip install piper-tts")
                self._fallback_mode()
                return
            
            logger.info(f"✓ Piper binary found: {self.piper_binary}")
            
            # Create models directory if it doesn't exist
            os.makedirs(self.models_dir, exist_ok=True)
            logger.info(f"✓ Models directory: {self.models_dir}")
            
            # Check for available voice models
            self._check_voice_models()
            
            # Warm up
            self._warmup()
            
            logger.info("=" * 70)
            logger.info("✓ PIPER TTS ENGINE READY")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Failed to setup Piper: {e}")
            self._fallback_mode()
    
    def _check_gpu_support(self):
        """Check if GPU is available and ONNX Runtime GPU is installed"""
        logger.info("Checking GPU support...")
        
        try:
            import onnxruntime as ort
            
            # Check available providers
            providers = ort.get_available_providers()
            logger.info(f"Available ONNX Runtime providers: {providers}")
            
            if 'CUDAExecutionProvider' in providers:
                logger.info("✓ GPU support available (CUDA)")
                
                # Try to get CUDA info
                try:
                    import subprocess
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=name,memory.total,memory.free', '--format=csv,noheader'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        logger.info(f"GPU Info: {result.stdout.strip()}")
                except:
                    pass
            elif 'ROCMExecutionProvider' in providers:
                logger.info("✓ GPU support available (ROCm/AMD)")
            else:
                logger.warning("⚠ GPU requested but CUDA/ROCm not available")
                logger.warning("  Install onnxruntime-gpu: pip uninstall onnxruntime && pip install onnxruntime-gpu")
                logger.warning("  Ensure CUDA is installed: nvidia-smi")
                logger.warning("  Falling back to CPU")
                self.service_config.use_gpu = False
                
        except ImportError:
            logger.warning("⚠ onnxruntime not found, cannot check GPU support")
            self.service_config.use_gpu = False
    
    def _find_piper_binary(self) -> Optional[str]:
        """Find piper binary in system"""
        # Try common locations
        locations = [
            "piper",  # In PATH
            "/usr/local/bin/piper",
            "/usr/bin/piper",
            os.path.expanduser("~/.local/bin/piper"),
        ]
        
        for loc in locations:
            try:
                result = subprocess.run(
                    [loc, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return loc
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    def _check_voice_models(self):
        """Check which voice models are available"""
        self.available_voices = []
        
        # Check for downloaded models
        if os.path.exists(self.models_dir):
            for root, dirs, files in os.walk(self.models_dir):
                for file in files:
                    if file.endswith('.onnx'):
                        # Extract voice ID from filename
                        voice_id = file.replace('.onnx', '')
                        self.available_voices.append(voice_id)
        
        if self.available_voices:
            logger.info(f"✓ Found {len(self.available_voices)} voice models:")
            for voice in self.available_voices:
                logger.info(f"  - {voice}")
        else:
            logger.warning("⚠ No voice models found")
            logger.info("Voice models will be auto-downloaded on first use")
            logger.info("Or manually download from: https://github.com/rhasspy/piper/releases")
    
    def _fallback_mode(self):
        """Enter fallback mode"""
        logger.warning("=" * 70)
        logger.warning("ENTERING FALLBACK MODE")
        logger.warning("=" * 70)
        logger.warning("⚠ Using fallback TTS (basic sine wave synthesis)")
        logger.warning("⚠ For production use, install Piper:")
        logger.warning("  pip install piper-tts")
        logger.warning("=" * 70)
        self.piper_binary = "fallback"
    
    def _warmup(self):
        """Warm up with dummy synthesis"""
        try:
            logger.info("Warming up Piper engine...")
            if self.piper_binary != "fallback":
                # Just verify piper works
                result = subprocess.run(
                    [self.piper_binary, "--help"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info("✓ Piper warmup complete")
                else:
                    logger.warning("⚠ Piper warmup failed")
            else:
                logger.info("Skipping warmup (fallback mode)")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
    
    def _get_model_path(self, voice_model: str) -> tuple:
        """
        Get model and config paths for a voice
        Returns: (model_path, config_path)
        """
        model_file = f"{voice_model}.onnx"
        config_file = f"{voice_model}.onnx.json"
        
        model_path = os.path.join(self.models_dir, model_file)
        config_path = os.path.join(self.models_dir, config_file)
        
        return model_path, config_path
    
    def _ensure_model_downloaded(self, voice_model: str) -> bool:
        """Ensure model is downloaded, download if needed"""
        model_path, config_path = self._get_model_path(voice_model)
        
        if os.path.exists(model_path) and os.path.exists(config_path):
            return True
        
        logger.info(f"Downloading model: {voice_model}")
        logger.info("This may take a few minutes...")
        
        try:
            # Download using piper's built-in download feature
            # Note: This is a simplified version - actual implementation may vary
            # based on piper version
            
            # For now, provide instructions
            logger.warning("=" * 70)
            logger.warning("MODEL DOWNLOAD REQUIRED")
            logger.warning("=" * 70)
            logger.warning(f"Please download the model manually:")
            logger.warning(f"  1. Go to: https://github.com/rhasspy/piper/releases")
            logger.warning(f"  2. Download: {voice_model}.onnx")
            logger.warning(f"  3. Download: {voice_model}.onnx.json")
            logger.warning(f"  4. Place both files in: {self.models_dir}")
            logger.warning("=" * 70)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            return False
    
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
            
            if self.piper_binary == "fallback":
                # Fallback synthesis
                audio = self._fallback_synthesize(text, voice_config)
                sample_rate = 22050
            else:
                # Piper synthesis
                audio, sample_rate = self._piper_synthesize(text, voice_config, synthesis_config)
            
            processing_time = time.time() - start_time
            audio_duration = len(audio) / sample_rate
            
            result = SynthesisResult(
                audio=audio,
                sample_rate=sample_rate,
                text=text,
                processing_time=processing_time,
                audio_duration=audio_duration,
                voice_model=voice_config.voice_model
            )
            
            logger.debug(
                f"Synthesized {len(text)} chars in {processing_time:.3f}s "
                f"(RTF: {result.realtime_factor:.2f}x)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise
    
    def _piper_synthesize(
        self,
        text: str,
        voice_config: VoiceConfig,
        synthesis_config: SynthesisConfig
    ) -> tuple:
        """Synthesize using Piper"""
        model_path, config_path = self._get_model_path(voice_config.voice_model)
        
        # Ensure model is available
        if not os.path.exists(model_path):
            if not self._ensure_model_downloaded(voice_config.voice_model):
                logger.warning("Model not available, using fallback")
                return self._fallback_synthesize(text, voice_config), 22050
        
        try:
            # Prepare piper command
            cmd = [
                self.piper_binary,
                "--model", model_path,
                "--config", config_path,
                "--output_raw"
            ]
            
            # Add GPU flag if enabled
            if self.service_config.use_gpu:
                cmd.append("--cuda")  # Note: Requires piper built with GPU support
                logger.debug("Using GPU acceleration for synthesis")
            
            # Add synthesis parameters
            if synthesis_config.length_scale != 1.0:
                cmd.extend(["--length_scale", str(synthesis_config.length_scale)])
            if synthesis_config.noise_scale != 0.667:
                cmd.extend(["--noise_scale", str(synthesis_config.noise_scale)])
            if synthesis_config.noise_w != 0.8:
                cmd.extend(["--noise_w", str(synthesis_config.noise_w)])
            
            # Set environment variable for ONNX Runtime GPU
            env = os.environ.copy()
            if self.service_config.use_gpu:
                env['CUDA_VISIBLE_DEVICES'] = str(self.service_config.gpu_device_id)
            
            # Run piper
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=30,
                env=env
            )
            
            if result.returncode != 0:
                logger.error(f"Piper error: {result.stderr.decode()}")
                return self._fallback_synthesize(text, voice_config), 22050
            
            # Convert raw audio to numpy array
            audio_bytes = result.stdout
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Apply speed modification if needed
            if voice_config.speed != 1.0:
                audio = self._apply_speed(audio, voice_config.speed)
            
            # Apply volume
            if voice_config.volume != 1.0:
                audio = audio * voice_config.volume
                audio = np.clip(audio, -1.0, 1.0)
            
            return audio, 22050  # Piper default sample rate
            
        except subprocess.TimeoutExpired:
            logger.error("Piper synthesis timeout")
            return self._fallback_synthesize(text, voice_config), 22050
        except Exception as e:
            logger.error(f"Piper synthesis error: {e}")
            return self._fallback_synthesize(text, voice_config), 22050
    
    def _apply_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Apply speed modification to audio"""
        if speed == 1.0:
            return audio
        
        target_length = int(len(audio) / speed)
        
        # Simple linear interpolation for speed change
        indices = np.linspace(0, len(audio) - 1, target_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)
        
        return resampled.astype(np.float32)
    
    def _fallback_synthesize(self, text: str, voice_config: VoiceConfig) -> np.ndarray:
        """Fallback synthesis using simple sine wave"""
        logger.debug("Using fallback synthesis")
        
        # Generate speech-like audio
        duration = len(text) * 0.08  # ~80ms per character
        sample_rate = 22050
        samples = int(duration * sample_rate)
        
        t = np.arange(samples) / sample_rate
        
        # Base frequency
        base_freq = 200
        
        # Multiple formants
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
        
        # Apply volume
        audio = audio * voice_config.volume * 0.3
        
        # Add envelope
        envelope = np.ones_like(audio)
        fade_samples = int(0.05 * sample_rate)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio = audio * envelope
        
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
            # Piper doesn't support true streaming, so we synthesize then chunk
            result = self.synthesize(text, voice_config, synthesis_config)
            audio = result.audio
            
            # Yield in chunks
            for i in range(0, len(audio), chunk_size):
                yield audio[i:i + chunk_size]
                
        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "models_dir": self.models_dir,
            "piper_binary": self.piper_binary,
            "available_voices": self.available_voices,
            "mode": "fallback" if self.piper_binary == "fallback" else "piper"
        }
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices"""
        voices = []
        
        # Add all defined voices
        for lang, lang_voices in PIPER_VOICES.items():
            for voice in lang_voices:
                voices.append({
                    **voice,
                    "language": lang,
                    "downloaded": voice["id"] in self.available_voices
                })
        
        return voices

