#!/usr/bin/env python3
"""
Integration example for Piper TTS Service
Shows how to use the service in your application with Hindi and English
"""

import asyncio
import json
import websockets
import base64
import wave


class PiperTTSClient:
    """Client for Piper TTS Service"""
    
    def __init__(self, host="localhost", port=8003):
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/stream"
    
    async def synthesize_streaming(
        self,
        text: str,
        voice_model: str = "en_US-lessac-medium",
        language: str = "en",
        on_audio_chunk=None,
        on_complete=None
    ):
        """
        Synthesize text with streaming output via WebSocket
        
        Args:
            text: Text to synthesize
            voice_model: Voice model ID
            language: Language code (en/hi)
            on_audio_chunk: Callback for audio chunks
            on_complete: Callback when synthesis complete
        """
        async with websockets.connect(self.ws_url) as websocket:
            # Send configuration
            config = {
                "type": "config",
                "voice": {
                    "voice_model": voice_model,
                    "language": language,
                    "speed": 1.0,
                    "volume": 1.0
                },
                "audio": {
                    "sample_rate": 22050,
                    "channels": 1,
                    "encoding": "pcm_s16le"
                },
                "streaming": {
                    "enabled": True,
                    "chunk_size": 1024
                }
            }
            
            await websocket.send(json.dumps(config))
            
            # Wait for ready
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") != "ready":
                raise Exception(f"Config failed: {response_data}")
            
            # Send text
            await websocket.send(json.dumps({
                "type": "text",
                "text": text
            }))
            
            # Receive audio chunks
            audio_chunks = []
            synthesis_started = False
            
            while True:
                try:
                    message = await websocket.recv()
                    
                    # Check if binary (audio) or text (metadata)
                    if isinstance(message, bytes):
                        # Audio chunk
                        audio_chunks.append(message)
                        if on_audio_chunk:
                            on_audio_chunk(message)
                    
                    else:
                        # JSON message
                        data = json.loads(message)
                        msg_type = data.get("type")
                        
                        if msg_type == "synthesis_start":
                            synthesis_started = True
                            print(f"Synthesizing: {data.get('char_count')} chars")
                        
                        elif msg_type == "audio_complete":
                            print(f"Synthesis complete: {data.get('processing_time', 0):.3f}s")
                            if on_complete:
                                on_complete(data)
                            break
                        
                        elif msg_type == "error":
                            raise Exception(f"Server error: {data.get('message')}")
                
                except websockets.exceptions.ConnectionClosed:
                    break
            
            return b''.join(audio_chunks)


async def example_english():
    """Example: English synthesis"""
    print("\n" + "=" * 60)
    print("Example 1: English Synthesis (Streaming)")
    print("=" * 60)
    
    client = PiperTTSClient()
    
    text = "Hello! This is an example of the Piper text to speech service. It supports streaming audio output for low latency applications."
    
    print(f"Text: {text[:50]}...")
    print(f"Voice: en_US-lessac-medium")
    
    # Synthesize with streaming
    audio_data = await client.synthesize_streaming(
        text=text,
        voice_model="en_US-lessac-medium",
        language="en",
        on_audio_chunk=lambda chunk: print(f"  Received chunk: {len(chunk)} bytes")
    )
    
    # Save to file
    with wave.open("example_english.wav", 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(audio_data)
    
    print(f"✓ Saved to: example_english.wav")


async def example_hindi():
    """Example: Hindi synthesis"""
    print("\n" + "=" * 60)
    print("Example 2: Hindi Synthesis (Streaming)")
    print("=" * 60)
    
    client = PiperTTSClient()
    
    text = "नमस्ते! यह पाइपर टेक्स्ट टू स्पीच सेवा का एक उदाहरण है। यह हिंदी और अंग्रेजी दोनों भाषाओं का समर्थन करता है।"
    
    print(f"Text: {text[:50]}...")
    print(f"Voice: hi_IN-madhur-medium")
    
    # Synthesize with streaming
    audio_data = await client.synthesize_streaming(
        text=text,
        voice_model="hi_IN-madhur-medium",
        language="hi",
        on_audio_chunk=lambda chunk: print(f"  Received chunk: {len(chunk)} bytes")
    )
    
    # Save to file
    with wave.open("example_hindi.wav", 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(audio_data)
    
    print(f"✓ Saved to: example_hindi.wav")


async def example_http_api():
    """Example: Using HTTP API (non-streaming)"""
    print("\n" + "=" * 60)
    print("Example 3: HTTP API (Non-streaming)")
    print("=" * 60)
    
    import requests
    
    # Simple HTTP request
    response = requests.post(
        "http://localhost:8003/synthesize",
        json={
            "text": "This is a simple HTTP API example.",
            "voice_config": {
                "voice_model": "en_US-amy-medium",
                "language": "en",
                "speed": 1.2
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Synthesis successful")
        print(f"  Duration: {data.get('audio_duration', 0):.3f}s")
        print(f"  Processing: {data.get('processing_time', 0):.3f}s")
        
        # Decode audio
        audio_bytes = base64.b64decode(data['audio_base64'])
        
        # Save to file
        with wave.open("example_http.wav", 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(audio_bytes)
        
        print(f"✓ Saved to: example_http.wav")
    else:
        print(f"✗ Request failed: {response.status_code}")


async def example_configurable_voices():
    """Example: Client-configurable voices"""
    print("\n" + "=" * 60)
    print("Example 4: Client-Configurable Voices")
    print("=" * 60)
    
    import requests
    
    # Get available voices
    response = requests.get("http://localhost:8003/voices")
    voices = response.json()['voices']
    
    print(f"Available voices: {len(voices)}")
    
    # Test different voices
    test_cases = [
        ("en_US-lessac-medium", "en", "Male US English voice"),
        ("en_US-amy-medium", "en", "Female US English voice"),
        ("hi_IN-madhur-medium", "hi", "Male Hindi voice"),
    ]
    
    for voice_model, language, description in test_cases:
        print(f"\n  Testing: {description}")
        print(f"  Voice: {voice_model}")
        
        # Check if voice is available
        voice_info = next((v for v in voices if v['id'] == voice_model), None)
        if not voice_info:
            print(f"    ⚠ Voice not available")
            continue
        
        text = "This is a test." if language == "en" else "यह एक परीक्षण है।"
        
        response = requests.post(
            "http://localhost:8003/synthesize",
            json={
                "text": text,
                "voice_config": {
                    "voice_model": voice_model,
                    "language": language
                }
            }
        )
        
        if response.status_code == 200:
            print(f"    ✓ Synthesis successful")
        else:
            print(f"    ✗ Synthesis failed")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("PIPER TTS SERVICE - INTEGRATION EXAMPLES")
    print("=" * 60)
    print("\nMake sure the service is running:")
    print("  ./start_service.sh")
    print("")
    
    try:
        # Run examples
        await example_english()
        await example_hindi()
        await example_http_api()
        await example_configurable_voices()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETE")
        print("=" * 60)
        print("\nGenerated audio files:")
        print("  - example_english.wav")
        print("  - example_hindi.wav")
        print("  - example_http.wav")
        print("\nPlay with: afplay <filename>.wav")
        print("")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure the service is running: ./start_service.sh")


if __name__ == "__main__":
    asyncio.run(main())

