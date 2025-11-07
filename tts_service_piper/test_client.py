#!/usr/bin/env python3
"""
Test client for Piper TTS Service
Tests both English and Hindi synthesis with different voices
"""

import requests
import json
import base64
import wave
import os
from typing import Optional

BASE_URL = "http://localhost:8003"


def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✓ Service is healthy")
            print(f"  Version: {data.get('version')}")
            print(f"  Service: {data.get('service')}")
            print(f"  Mode: {data.get('mode', 'N/A')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to service: {e}")
        return False


def test_list_voices():
    """Test list voices endpoint"""
    print("\n" + "=" * 60)
    print("Testing List Voices Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/voices")
        if response.status_code == 200:
            data = response.json()
            voices = data.get('voices', [])
            print(f"✓ Found {data.get('count', 0)} voices:")
            
            # Group by language
            english_voices = [v for v in voices if v.get('language') == 'en']
            hindi_voices = [v for v in voices if v.get('language') == 'hi']
            
            if english_voices:
                print("\n  English Voices:")
                for voice in english_voices:
                    downloaded = "✓" if voice.get('downloaded', False) else "⚠"
                    print(f"    {downloaded} {voice['id']} - {voice['name']} ({voice['gender']})")
            
            if hindi_voices:
                print("\n  Hindi Voices:")
                for voice in hindi_voices:
                    downloaded = "✓" if voice.get('downloaded', False) else "⚠"
                    print(f"    {downloaded} {voice['id']} - {voice['name']} ({voice['gender']})")
            
            return voices
        else:
            print(f"✗ Failed to list voices: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error listing voices: {e}")
        return []


def test_synthesize(text: str, voice_model: str, language: str, output_file: Optional[str] = None):
    """Test synthesize endpoint"""
    print(f"\n{'=' * 60}")
    print(f"Testing Synthesis: {language.upper()}")
    print("=" * 60)
    print(f"Text: {text[:50]}...")
    print(f"Voice: {voice_model}")
    
    try:
        # Prepare request
        request_data = {
            "text": text,
            "voice_config": {
                "voice_model": voice_model,
                "language": language,
                "speed": 1.0,
                "volume": 1.0
            },
            "audio_config": {
                "sample_rate": 22050,
                "channels": 1,
                "encoding": "pcm_s16le"
            }
        }
        
        # Send request
        response = requests.post(
            f"{BASE_URL}/synthesize",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Synthesis successful")
            print(f"  Processing time: {data.get('processing_time', 0):.3f}s")
            print(f"  Audio duration: {data.get('audio_duration', 0):.3f}s")
            print(f"  RTF: {data.get('realtime_factor', 0):.3f}x")
            
            # Save audio if output file specified
            if output_file:
                audio_base64 = data.get('audio_base64', '')
                audio_bytes = base64.b64decode(audio_base64)
                
                # Save as WAV file
                with wave.open(output_file, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(22050)
                    wav_file.writeframes(audio_bytes)
                
                print(f"  ✓ Audio saved to: {output_file}")
            
            return True
        else:
            print(f"✗ Synthesis failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Synthesis error: {e}")
        return False


def test_get_config():
    """Test get default config endpoint"""
    print("\n" + "=" * 60)
    print("Testing Get Default Config")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/config/defaults")
        if response.status_code == 200:
            data = response.json()
            print("✓ Default configuration retrieved")
            print(f"  Audio sample rate: {data.get('audio', {}).get('sample_rate')}Hz")
            print(f"  Default voice: {data.get('voice', {}).get('voice_model')}")
            print(f"  Streaming enabled: {data.get('streaming', {}).get('enabled')}")
            return True
        else:
            print(f"✗ Failed to get config: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting config: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PIPER TTS SERVICE TEST SUITE")
    print("=" * 60)
    
    # Create output directory
    os.makedirs("test_output", exist_ok=True)
    
    # Test 1: Health check
    if not test_health():
        print("\n✗ Service is not available. Please start the service first.")
        return
    
    # Test 2: List voices
    voices = test_list_voices()
    
    # Test 3: Get default config
    test_get_config()
    
    # Test 4: English synthesis
    test_synthesize(
        text="Hello, this is a test of the Piper text to speech service. How does it sound?",
        voice_model="en_US-lessac-medium",
        language="en",
        output_file="test_output/english_test.wav"
    )
    
    # Test 5: Hindi synthesis
    test_synthesize(
        text="नमस्ते, यह पाइपर टेक्स्ट टू स्पीच सेवा का परीक्षण है।",
        voice_model="hi_IN-madhur-medium",
        language="hi",
        output_file="test_output/hindi_test.wav"
    )
    
    # Test 6: Different speed
    print("\n" + "=" * 60)
    print("Testing with Different Speed (1.5x)")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/synthesize",
            json={
                "text": "This is a faster speech test.",
                "voice_config": {
                    "voice_model": "en_US-lessac-medium",
                    "language": "en",
                    "speed": 1.5
                }
            }
        )
        if response.status_code == 200:
            print("✓ Speed modification test passed")
        else:
            print(f"✗ Speed test failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Speed test error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
    print("\nGenerated audio files in: test_output/")
    print("  - english_test.wav")
    print("  - hindi_test.wav")
    print("\nPlay audio files with:")
    print("  macOS: afplay test_output/english_test.wav")
    print("  Linux: aplay test_output/english_test.wav")
    print("")


if __name__ == "__main__":
    main()

