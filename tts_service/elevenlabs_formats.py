#!/usr/bin/env python3
"""
ElevenLabs output format definitions
Complete list of supported formats
"""

from typing import List, Dict

# All supported output formats (ElevenLabs-compatible)
SUPPORTED_OUTPUT_FORMATS = {
    # MP3 formats
    "mp3_22050_32": {
        "codec": "mp3",
        "sample_rate": 22050,
        "bitrate": 32,
        "description": "MP3 with 22.05kHz sample rate at 32kbps",
        "tier": "free"
    },
    "mp3_44100_32": {
        "codec": "mp3",
        "sample_rate": 44100,
        "bitrate": 32,
        "description": "MP3 with 44.1kHz sample rate at 32kbps",
        "tier": "free"
    },
    "mp3_44100_64": {
        "codec": "mp3",
        "sample_rate": 44100,
        "bitrate": 64,
        "description": "MP3 with 44.1kHz sample rate at 64kbps",
        "tier": "free"
    },
    "mp3_44100_96": {
        "codec": "mp3",
        "sample_rate": 44100,
        "bitrate": 96,
        "description": "MP3 with 44.1kHz sample rate at 96kbps",
        "tier": "free"
    },
    "mp3_44100_128": {
        "codec": "mp3",
        "sample_rate": 44100,
        "bitrate": 128,
        "description": "MP3 with 44.1kHz sample rate at 128kbps (default)",
        "tier": "free"
    },
    "mp3_44100_192": {
        "codec": "mp3",
        "sample_rate": 44100,
        "bitrate": 192,
        "description": "MP3 with 44.1kHz sample rate at 192kbps",
        "tier": "creator"
    },
    
    # PCM formats
    "pcm_16000": {
        "codec": "pcm",
        "sample_rate": 16000,
        "bitrate": None,
        "description": "PCM with 16kHz sample rate",
        "tier": "free"
    },
    "pcm_22050": {
        "codec": "pcm",
        "sample_rate": 22050,
        "bitrate": None,
        "description": "PCM with 22.05kHz sample rate",
        "tier": "free"
    },
    "pcm_24000": {
        "codec": "pcm",
        "sample_rate": 24000,
        "bitrate": None,
        "description": "PCM with 24kHz sample rate",
        "tier": "free"
    },
    "pcm_44100": {
        "codec": "pcm",
        "sample_rate": 44100,
        "bitrate": None,
        "description": "PCM with 44.1kHz sample rate",
        "tier": "pro"
    },
    "pcm_48000": {
        "codec": "pcm",
        "sample_rate": 48000,
        "bitrate": None,
        "description": "PCM with 48kHz sample rate",
        "tier": "pro"
    },
    
    # μ-law format (Twilio)
    "ulaw_8000": {
        "codec": "ulaw",
        "sample_rate": 8000,
        "bitrate": None,
        "description": "μ-law with 8kHz sample rate (Twilio compatible)",
        "tier": "free"
    },
    
    # A-law format
    "alaw_8000": {
        "codec": "alaw",
        "sample_rate": 8000,
        "bitrate": None,
        "description": "A-law with 8kHz sample rate",
        "tier": "free"
    },
}

# Default format (matches ElevenLabs)
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"


def validate_output_format(format_string: str) -> bool:
    """Check if output format is valid"""
    return format_string in SUPPORTED_OUTPUT_FORMATS


def get_format_info(format_string: str) -> Dict:
    """Get format information"""
    return SUPPORTED_OUTPUT_FORMATS.get(format_string, SUPPORTED_OUTPUT_FORMATS[DEFAULT_OUTPUT_FORMAT])


def list_formats() -> List[str]:
    """List all supported formats"""
    return list(SUPPORTED_OUTPUT_FORMATS.keys())