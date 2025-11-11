#!/usr/bin/env python3
"""
ElevenLabs-compatible request/response models
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VoiceSettings(BaseModel):
    """ElevenLabs voice settings"""
    stability: float = Field(default=0.5, ge=0.0, le=1.0, description="Stability setting")
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0, description="Similarity boost")
    style: float = Field(default=0.0, ge=0.0, le=1.0, description="Style setting")
    use_speaker_boost: bool = Field(default=True, description="Use speaker boost")


class TextToSpeechRequest(BaseModel):
    """ElevenLabs-compatible TTS request"""
    text: str = Field(..., description="Text to synthesize")
    model_id: Optional[str] = Field(default="eleven_multilingual_v2", description="Model ID")
    voice_settings: Optional[VoiceSettings] = Field(default_factory=VoiceSettings, description="Voice settings")
    language_code: Optional[str] = Field(default=None, description="Language code (optional)")


class Voice(BaseModel):
    """ElevenLabs-compatible voice model"""
    voice_id: str = Field(..., description="Unique voice ID")
    name: str = Field(..., description="Voice name")
    samples: Optional[List[Dict[str, Any]]] = Field(default=None, description="Voice samples")
    category: Optional[str] = Field(default=None, description="Voice category")
    fine_tuning: Optional[Dict[str, Any]] = Field(default=None, description="Fine-tuning info")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Voice labels")
    description: Optional[str] = Field(default=None, description="Voice description")
    preview_url: Optional[str] = Field(default=None, description="Preview audio URL")
    available_for_tiers: Optional[List[str]] = Field(default=None, description="Available tiers")
    settings: Optional[VoiceSettings] = Field(default=None, description="Voice settings")
    sharing: Optional[Dict[str, Any]] = Field(default=None, description="Sharing info")
    high_quality_base_model_ids: Optional[List[str]] = Field(default=None, description="High quality base models")
    safety_control: Optional[str] = Field(default=None, description="Safety control")
    permission_on_resource: Optional[str] = Field(default=None, description="Permission")
    voice_verification: Optional[Dict[str, Any]] = Field(default=None, description="Verification info")
    play_back_preview: Optional[bool] = Field(default=None, description="Playback preview")


class VoicesResponse(BaseModel):
    """ElevenLabs voices list response"""
    voices: List[Voice] = Field(..., description="List of voices")


class Model(BaseModel):
    """ElevenLabs-compatible model"""
    model_id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    can_be_finetuned: bool = Field(default=False, description="Can be fine-tuned")
    can_do_text_to_speech: bool = Field(default=True, description="Supports TTS")
    can_do_voice_conversion: bool = Field(default=False, description="Supports voice conversion")
    can_use_speaker_boost: bool = Field(default=True, description="Supports speaker boost")
    serves_pro_voices: bool = Field(default=False, description="Serves pro voices")
    token_cost_factor: float = Field(default=1.0, description="Token cost factor")
    description: Optional[str] = Field(default=None, description="Model description")
    languages: Optional[List[Dict[str, Any]]] = Field(default=None, description="Supported languages")
    max_characters_request_free_user: Optional[int] = Field(default=None, description="Max chars for free users")
    max_characters_request_subscribed_user: Optional[int] = Field(default=None, description="Max chars for subscribed users")
    requires_alpha_access: bool = Field(default=False, description="Requires alpha access")
    is_private: bool = Field(default=False, description="Is private model")
    can_use_style: bool = Field(default=False, description="Can use style")
    can_use_pronunciation_dictionary: bool = Field(default=False, description="Can use pronunciation dictionary")


class ModelsResponse(BaseModel):
    """ElevenLabs models list response"""
    models: List[Model] = Field(..., description="List of models")


class ErrorResponse(BaseModel):
    """ElevenLabs-compatible error response"""
    detail: Dict[str, Any] = Field(..., description="Error details")

