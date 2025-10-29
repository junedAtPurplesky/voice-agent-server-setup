#!/bin/bash
# Script to recreate all remaining Python files

echo "Creating remaining Python application files..."

# Create vad.py
cat > app/vad.py << 'EOF'
"""
Voice Activity Detection (VAD) implementation
Handles real-time VAD for WebSocket streaming with configurable parameters
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, Optional, Callable, List
from collections import deque
import librosa
from .config import VADConfig, config_manager

logger = logging.getLogger(__name__)


class VADDetector:
    """Voice Activity Detection using librosa"""
    
    def __init__(self, config: VADConfig):
        self.config = config
        self.sample_rate = 16000
        self.frame_length = 1024
        self.hop_length = 512
        
        # VAD state
        self.is_speaking = False
        self.silence_frames = 0
        self.speech_frames = 0
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 2))
        
        # Calculate frame thresholds
        self.min_speech_frames = int(config.min_speech_duration_ms * self.sample_rate / 1000 / self.hop_length)
        self.min_silence_frames = int(config.min_silence_duration_ms * self.sample_rate / 1000 / self.hop_length)
        
        logger.info(f"VAD initialized: threshold={config.threshold}")
    
    def _calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """Calculate RMS energy of audio chunk"""
        if len(audio_chunk) == 0:
            return 0.0
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        return float(rms)
    
    def detect_voice_activity(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """Detect voice activity in audio chunk"""
        if len(audio_chunk) == 0:
            return {"is_speech": False, "confidence": 0.0, "state": "silence"}
        
        energy = self._calculate_energy(audio_chunk)
        is_speech = energy > self.config.threshold
        
        if is_speech:
            self.speech_frames += 1
            self.silence_frames = 0
        else:
            self.silence_frames += 1
            self.speech_frames = 0
        
        if not self.is_speaking and self.speech_frames >= self.min_speech_frames:
            self.is_speaking = True
            state = "speech_start"
        elif self.is_speaking and self.silence_frames >= self.min_silence_frames:
            self.is_speaking = False
            state = "speech_end"
        elif self.is_speaking:
            state = "speaking"
        else:
            state = "silence"
        
        return {
            "is_speech": is_speech,
            "confidence": min(1.0, energy * 2),
            "state": state,
            "is_speaking": self.is_speaking
        }


class WebSocketVAD:
    """VAD for WebSocket streaming"""
    
    def __init__(self, config: VADConfig):
        self.config = config
        self.detector = VADDetector(config)
        self.is_active = False
        self.speech_segments = 0
        
    async def process_audio_chunk(self, audio_data: bytes) -> Optional[Dict[str, Any]]:
        """Process audio chunk and return VAD events"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            vad_result = self.detector.detect_voice_activity(audio_array)
            
            if vad_result["state"] == "speech_start":
                self.speech_segments += 1
                self.is_active = True
            elif vad_result["state"] == "speech_end":
                self.is_active = False
            
            vad_result["timestamp"] = asyncio.get_event_loop().time()
            return vad_result
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
            return None
    
    def reset(self):
        """Reset VAD state"""
        self.detector.is_speaking = False
        self.detector.silence_frames = 0
        self.detector.speech_frames = 0
        self.is_active = False


class VADManager:
    """Manages VAD instances for different clients"""
    
    def __init__(self):
        self.vad_instances: Dict[str, WebSocketVAD] = {}
        self.config = config_manager.get_config()
    
    def create_vad_instance(self, client_id: str, config: Optional[VADConfig] = None) -> WebSocketVAD:
        """Create new VAD instance for client"""
        if config is None:
            config = self.config.transcription.vad_config
        
        vad = WebSocketVAD(config)
        self.vad_instances[client_id] = vad
        logger.info(f"Created VAD instance for client: {client_id}")
        return vad
    
    def get_vad_instance(self, client_id: str) -> Optional[WebSocketVAD]:
        """Get VAD instance for client"""
        return self.vad_instances.get(client_id)
    
    def remove_vad_instance(self, client_id: str):
        """Remove VAD instance for client"""
        if client_id in self.vad_instances:
            del self.vad_instances[client_id]
            logger.info(f"Removed VAD instance for client: {client_id}")
    
    def get_active_clients(self) -> List[str]:
        """Get list of active client IDs"""
        return list(self.vad_instances.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get VAD manager statistics"""
        return {
            "active_clients": len(self.vad_instances),
            "client_ids": list(self.vad_instances.keys())
        }


# Global VAD manager instance
vad_manager = VADManager()
EOF

echo "✅ Created vad.py"
