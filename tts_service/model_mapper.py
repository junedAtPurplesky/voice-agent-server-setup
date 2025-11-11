#!/usr/bin/env python3
"""
Model name mapping between CosyVoice and ElevenLabs-style names
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# Mapping from ElevenLabs model IDs to CosyVoice model names
ELEVENLABS_TO_COSYVOICE: Dict[str, str] = {
    "eleven_multilingual_v2": "CosyVoice-300M-SFT",
    "eleven_turbo_v2_5": "CosyVoice-300M-SFT",  # Use same model for turbo
    "eleven_turbo_v2": "CosyVoice-300M-SFT",
    "eleven_monolingual_v1": "CosyVoice-300M-SFT",
    "eleven_multilingual_v1": "CosyVoice-300M-SFT",
    "eleven_multilingual_v2_5": "CosyVoice-300M-SFT",
}

# Reverse mapping
COSYVOICE_TO_ELEVENLABS: Dict[str, str] = {
    "CosyVoice-300M-SFT": "eleven_multilingual_v2",
    "CosyVoice-300M": "eleven_multilingual_v2",
    "CosyVoice-0.5B": "eleven_turbo_v2_5",
}

# Default model
DEFAULT_ELEVENLABS_MODEL = "eleven_multilingual_v2"


class ModelMapper:
    """Maps between ElevenLabs and CosyVoice model names"""
    
    @staticmethod
    def elevenlabs_to_cosyvoice(elevenlabs_model: str) -> str:
        """
        Convert ElevenLabs model ID to CosyVoice model name
        
        Args:
            elevenlabs_model: ElevenLabs model ID (e.g., "eleven_multilingual_v2")
            
        Returns:
            CosyVoice model name
        """
        return ELEVENLABS_TO_COSYVOICE.get(
            elevenlabs_model,
            ELEVENLABS_TO_COSYVOICE[DEFAULT_ELEVENLABS_MODEL]
        )
    
    @staticmethod
    def cosyvoice_to_elevenlabs(cosyvoice_model: str) -> str:
        """
        Convert CosyVoice model name to ElevenLabs model ID
        
        Args:
            cosyvoice_model: CosyVoice model name
            
        Returns:
            ElevenLabs model ID
        """
        return COSYVOICE_TO_ELEVENLABS.get(
            cosyvoice_model,
            DEFAULT_ELEVENLABS_MODEL
        )
    
    @staticmethod
    def is_valid_elevenlabs_model(model_id: str) -> bool:
        """Check if model ID is a valid ElevenLabs model"""
        return model_id in ELEVENLABS_TO_COSYVOICE
    
    @staticmethod
    def get_default_model() -> str:
        """Get default ElevenLabs model ID"""
        return DEFAULT_ELEVENLABS_MODEL


# Available ElevenLabs models for API
AVAILABLE_MODELS = [
    {
        "model_id": "eleven_multilingual_v2",
        "name": "Eleven Multilingual v2",
        "can_be_finetuned": False,
        "can_do_text_to_speech": True,
        "can_do_voice_conversion": False,
        "can_use_speaker_boost": True,
        "serves_pro_voices": False,
        "token_cost_factor": 1.0,
        "description": "Multilingual model supporting multiple languages",
        "languages": [
            {"language_id": "en", "name": "English"},
            {"language_id": "zh", "name": "Chinese"},
            {"language_id": "ja", "name": "Japanese"},
            {"language_id": "ko", "name": "Korean"},
        ],
        "max_characters_request_free_user": 5000,
        "max_characters_request_subscribed_user": 50000,
        "requires_alpha_access": False,
        "is_private": False,
        "can_use_style": False,
        "can_use_pronunciation_dictionary": False,
    },
    {
        "model_id": "eleven_turbo_v2_5",
        "name": "Eleven Turbo v2.5",
        "can_be_finetuned": False,
        "can_do_text_to_speech": True,
        "can_do_voice_conversion": False,
        "can_use_speaker_boost": True,
        "serves_pro_voices": False,
        "token_cost_factor": 0.5,
        "description": "Fast, low-latency model optimized for real-time applications",
        "languages": [
            {"language_id": "en", "name": "English"},
            {"language_id": "zh", "name": "Chinese"},
            {"language_id": "ja", "name": "Japanese"},
            {"language_id": "ko", "name": "Korean"},
        ],
        "max_characters_request_free_user": 5000,
        "max_characters_request_subscribed_user": 50000,
        "requires_alpha_access": False,
        "is_private": False,
        "can_use_style": False,
        "can_use_pronunciation_dictionary": False,
    },
]

