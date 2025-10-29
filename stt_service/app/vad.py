"""Voice Activity Detection"""
import logging
import numpy as np
from typing import Dict, Any, Optional, List
from .config import VADConfig, config_manager

logger = logging.getLogger(__name__)

class VADDetector:
    def __init__(self, config: VADConfig):
        self.config = config
        self.is_speaking = False
    
    def detect_voice_activity(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        if len(audio_chunk) == 0:
            return {"is_speech": False, "confidence": 0.0, "state": "silence"}
        energy = float(np.sqrt(np.mean(audio_chunk ** 2)))
        is_speech = energy > self.config.threshold
        state = "speaking" if is_speech else "silence"
        return {"is_speech": is_speech, "confidence": min(1.0, energy * 2), "state": state}

class WebSocketVAD:
    def __init__(self, config: VADConfig):
        self.config = config
        self.detector = VADDetector(config)
    
    async def process_audio_chunk(self, audio_data: bytes) -> Optional[Dict[str, Any]]:
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            return self.detector.detect_voice_activity(audio_array)
        except:
            return None
    
    def reset(self):
        self.detector.is_speaking = False

class VADManager:
    def __init__(self):
        self.vad_instances: Dict[str, WebSocketVAD] = {}
        self.config = config_manager.get_config()
    
    def create_vad_instance(self, client_id: str, config: Optional[VADConfig] = None) -> WebSocketVAD:
        vad = WebSocketVAD(config or self.config.transcription.vad_config)
        self.vad_instances[client_id] = vad
        return vad
    
    def remove_vad_instance(self, client_id: str):
        if client_id in self.vad_instances:
            del self.vad_instances[client_id]
    
    def get_active_clients(self) -> List[str]:
        return list(self.vad_instances.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        return {"active_clients": len(self.vad_instances)}

vad_manager = VADManager()
