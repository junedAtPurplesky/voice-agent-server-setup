#!/usr/bin/env python3
"""
Test client for Faster Whisper STT Service
Demonstrates configuration options and both simple and streaming modes
"""

import asyncio
import json
import wave
import sys
import time
from pathlib import Path

import requests
import websockets
import numpy as np


STT_SERVICE_URL = "http://localhost:8001"
STT_WEBSOCKET_URL = "ws://localhost:8001/stream"


def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{STT_SERVICE_URL}/health")
        response.raise_for_status()
        result = response.json()
        print(f"✓ Health check: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_get_default_config():
    """Test getting default configuration"""
    print("\nTesting default config endpoint...")
    try:
        response = requests.get(f"{STT_SERVICE_URL}/config/defaults")
        response.raise_for_status()
        result = response.json()
        print(f"✓ Default config:")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        print(f"✗ Failed to get default config: {e}")
        return False


def generate_test_audio(duration: float = 3.0, sample_rate: int = 16000) -> bytes:
    """Generate test audio (sine wave tone)"""
    samples = int(duration * sample_rate)
    frequency = 440.0  # A4 note
    
    audio = np.sin(2 * np.pi * frequency * np.arange(samples) / sample_rate)
    audio = (audio * 32767).astype(np.int16)
    
    return audio.tobytes()


def create_wav_file(audio_bytes: bytes, filename: str, sample_rate: int = 16000):
    """Create a WAV file from raw audio bytes"""
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)


def test_simple_transcription():
    """Test simple transcription endpoint"""
    print("\nTesting simple transcription endpoint...")
    
    audio_bytes = generate_test_audio(duration=2.0)
    test_file = "test_audio.wav"
    create_wav_file(audio_bytes, test_file)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            response = requests.post(
                f"{STT_SERVICE_URL}/transcribe",
                files=files,
                data={'language': 'en', 'beam_size': 5}
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Transcription result:")
            print(f"  Text: {result.get('text', 'N/A')}")
            print(f"  Language: {result.get('language', 'N/A')}")
            print(f"  Processing time: {result.get('processing_time', 0):.3f}s")
            print(f"  RTF: {result.get('realtime_factor', 0):.2f}x")
            
            return True
    except Exception as e:
        print(f"✗ Simple transcription failed: {e}")
        return False
    finally:
        Path(test_file).unlink(missing_ok=True)


async def test_streaming_with_default_config():
    """Test streaming with default configuration"""
    print("\nTesting streaming with default config...")
    
    audio_bytes = generate_test_audio(duration=5.0)
    
    try:
        async with websockets.connect(STT_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Don't send config - use defaults
            
            # Send audio in chunks
            chunk_size = 3200  # 100ms chunks
            chunks = [audio_bytes[i:i+chunk_size] for i in range(0, len(audio_bytes), chunk_size)]
            
            print(f"Sending {len(chunks)} audio chunks...")
            
            async def receive_messages():
                messages = []
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        messages.append(data)
                        
                        msg_type = data.get('type')
                        if msg_type == 'partial':
                            print(f"  [Partial] {data.get('text', '')}")
                        elif msg_type == 'final':
                            print(f"  [Final] {data.get('text', '')}")
                        elif msg_type == 'end_of_utterance':
                            print("  [End of utterance]")
                        elif msg_type == 'status':
                            if data.get('is_speaking'):
                                print(f"  [Status] Speaking... ({data.get('speech_duration', 0):.1f}s)")
                                
                except websockets.exceptions.ConnectionClosed:
                    pass
                return messages
            
            receive_task = asyncio.create_task(receive_messages())
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                await websocket.send(chunk)
                await asyncio.sleep(0.1)
                
                if i == len(chunks) // 2:
                    print("  [Simulating silence...]")
                    await asyncio.sleep(2.0)
            
            await asyncio.sleep(2.0)
            receive_task.cancel()
            
            try:
                messages = await receive_task
                print(f"✓ Received {len(messages)} messages")
            except asyncio.CancelledError:
                pass
            
            return True
            
    except Exception as e:
        print(f"✗ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_with_custom_config():
    """Test streaming with custom configuration"""
    print("\nTesting streaming with custom config...")
    
    # Custom configuration
    custom_config = {
        "type": "config",
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "encoding": "pcm_s16le"
        },
        "vad": {
            "enabled": True,
            "mode": 2,  # Less aggressive
            "silence_duration": 0.8,  # Shorter silence threshold
            "min_speech_duration": 0.2,
            "frame_duration": 30
        },
        "transcription": {
            "language": "en",
            "beam_size": 5,
            "enable_partial_transcripts": True,
            "partial_interval": 0.3  # More frequent partials
        }
    }
    
    audio_bytes = generate_test_audio(duration=4.0)
    
    try:
        async with websockets.connect(STT_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send configuration
            print("Sending custom configuration...")
            await websocket.send(json.dumps(custom_config))
            
            # Wait for ready confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'ready':
                print(f"✓ Session configured: {data.get('message')}")
            else:
                print(f"✗ Unexpected response: {data}")
                return False
            
            # Send audio
            chunk_size = 3200
            chunks = [audio_bytes[i:i+chunk_size] for i in range(0, len(audio_bytes), chunk_size)]
            
            print(f"Sending {len(chunks)} audio chunks with custom config...")
            
            async def receive_messages():
                messages = []
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        messages.append(data)
                        
                        msg_type = data.get('type')
                        if msg_type == 'partial':
                            print(f"  [Partial] {data.get('text', '')}")
                        elif msg_type == 'final':
                            print(f"  [Final] {data.get('text', '')}")
                            print(f"    RTF: {data.get('realtime_factor', 0):.2f}x")
                        elif msg_type == 'end_of_utterance':
                            print("  [End of utterance]")
                        elif msg_type == 'status':
                            pass  # Skip status messages for brevity
                                
                except websockets.exceptions.ConnectionClosed:
                    pass
                return messages
            
            receive_task = asyncio.create_task(receive_messages())
            
            for i, chunk in enumerate(chunks):
                await websocket.send(chunk)
                await asyncio.sleep(0.1)
                
                if i == len(chunks) // 2:
                    print("  [Pause...]")
                    await asyncio.sleep(1.5)
            
            await asyncio.sleep(2.0)
            receive_task.cancel()
            
            try:
                messages = await receive_task
                print(f"✓ Received {len(messages)} messages with custom config")
            except asyncio.CancelledError:
                pass
            
            return True
            
    except Exception as e:
        print(f"✗ Custom config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_control_messages():
    """Test control messages (reset, force_end, get_stats)"""
    print("\nTesting control messages...")
    
    audio_bytes = generate_test_audio(duration=3.0)
    
    try:
        async with websockets.connect(STT_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send some audio
            chunk_size = 3200
            chunks = [audio_bytes[i:i+chunk_size] for i in range(0, len(audio_bytes), chunk_size)]
            
            for i, chunk in enumerate(chunks[:10]):  # Just send a few chunks
                await websocket.send(chunk)
                await asyncio.sleep(0.05)
            
            # Test get_stats
            print("\n  Testing get_stats...")
            await websocket.send(json.dumps({"type": "get_stats"}))
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            stats = json.loads(response)
            if stats.get('type') == 'stats':
                print(f"  ✓ Stats: {json.dumps(stats, indent=4)}")
            
            # Test reset
            print("\n  Testing reset...")
            await websocket.send(json.dumps({"type": "reset"}))
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            reset_resp = json.loads(response)
            if reset_resp.get('type') == 'status':
                print(f"  ✓ Reset: {reset_resp.get('message')}")
            
            # Send more audio
            for chunk in chunks[10:15]:
                await websocket.send(chunk)
                await asyncio.sleep(0.05)
            
            # Test force_end
            print("\n  Testing force_end...")
            await websocket.send(json.dumps({"type": "force_end"}))
            
            # Wait for responses
            await asyncio.sleep(1.0)
            
            # Drain messages
            messages = []
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    messages.append(json.loads(msg))
            except asyncio.TimeoutError:
                pass
            
            print(f"  ✓ Received {len(messages)} responses")
            
            return True
            
    except Exception as e:
        print(f"✗ Control messages test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 70)
    print("Faster Whisper STT Service - Test Suite v2.0")
    print("Testing modular architecture with client-side configuration")
    print("=" * 70)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Get default config
    results.append(("Get Default Config", test_get_default_config()))
    
    # Test 3: Simple transcription
    results.append(("Simple Transcription", test_simple_transcription()))
    
    # Test 4: Streaming with defaults
    results.append(("Streaming (Default Config)", await test_streaming_with_default_config()))
    
    # Test 5: Streaming with custom config
    results.append(("Streaming (Custom Config)", await test_streaming_with_custom_config()))
    
    # Test 6: Control messages
    results.append(("Control Messages", await test_control_messages()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return all(p for _, p in results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
