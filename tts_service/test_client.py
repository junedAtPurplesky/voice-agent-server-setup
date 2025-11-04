#!/usr/bin/env python3
"""
Test client for CosyVoice2 TTS Service
Comprehensive testing of HTTP and WebSocket APIs
"""

import asyncio
import json
import sys
import time
import base64
import wave
from pathlib import Path

import requests
import websockets
import numpy as np


TTS_SERVICE_URL = "http://localhost:8002"
TTS_WEBSOCKET_URL = "ws://localhost:8002/stream"

# Test texts
TEST_TEXTS = {
    "short": "Hello, world! This is a test of the text-to-speech service.",
    "medium": "The quick brown fox jumps over the lazy dog. This is a longer sentence to test the quality of speech synthesis. It contains multiple sentences with various punctuation marks, including commas, periods, and exclamation points!",
    "long": "Text-to-speech technology has come a long way in recent years. Modern systems can produce natural-sounding speech that is nearly indistinguishable from human voices. These systems are used in a wide variety of applications, from virtual assistants to audiobook narration. The quality and naturalness of synthetic speech continues to improve with advances in machine learning and neural network architectures.",
    "numbers": "The total cost is $42.50. The temperature is 72° Fahrenheit. That's about 50% off the original price!",
    "multi_sentence": "First sentence. Second sentence! Third sentence? Fourth sentence, with a comma. Fifth and final sentence."
}


def save_audio(audio_bytes: bytes, filename: str, sample_rate: int = 24000):
    """Save audio bytes as WAV file"""
    try:
        # Convert to int16 if needed
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_np.tobytes())
        
        print(f"✓ Saved audio: {filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to save audio: {e}")
        return False


def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{TTS_SERVICE_URL}/health")
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
        response = requests.get(f"{TTS_SERVICE_URL}/config/defaults")
        response.raise_for_status()
        result = response.json()
        print(f"✓ Default config:")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        print(f"✗ Failed to get default config: {e}")
        return False


def test_list_voices():
    """Test listing available voices"""
    print("\nTesting list voices endpoint...")
    try:
        response = requests.get(f"{TTS_SERVICE_URL}/voices")
        response.raise_for_status()
        result = response.json()
        print(f"✓ Available voices: {result['count']}")
        for voice in result['voices']:
            print(f"   - {voice['id']}: {voice['name']} ({voice['gender']}, {voice['language']})")
        return True
    except Exception as e:
        print(f"✗ Failed to list voices: {e}")
        return False


def test_simple_synthesis():
    """Test simple HTTP TTS synthesis"""
    print("\nTesting simple HTTP synthesis...")
    print("=" * 60)
    
    try:
        request_data = {
            "text": TEST_TEXTS["short"],
            "voice_config": {
                "speaker": "default",
                "speed": 1.0,
                "pitch": 1.0
            },
            "audio_config": {
                "sample_rate": 24000,
                "encoding": "pcm_s16le"
            }
        }
        
        start_time = time.time()
        response = requests.post(
            f"{TTS_SERVICE_URL}/synthesize",
            json=request_data
        )
        response.raise_for_status()
        result = response.json()
        request_time = time.time() - start_time
        
        print(f"\n✓ HTTP Synthesis Success!")
        print(f"\n📝 INPUT TEXT:")
        print(f"   \"{request_data['text']}\"")
        
        print(f"\n📊 Metadata:")
        print(f"   Text length: {len(request_data['text'])} chars")
        print(f"   Audio duration: {result.get('audio_duration', 0):.2f}s")
        print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
        print(f"   Request time: {request_time:.3f}s")
        print(f"   Real-time factor: {result.get('realtime_factor', 0):.2f}x")
        print(f"   Speaker: {result.get('speaker', 'N/A')}")
        
        # Decode and save audio
        if result.get('audio_base64'):
            audio_bytes = base64.b64decode(result['audio_base64'])
            print(f"   Audio size: {len(audio_bytes):,} bytes")
            save_audio(audio_bytes, "test_output_http.wav", result.get('sample_rate', 24000))
        
        print("=" * 60)
        return True
    except Exception as e:
        print(f"✗ Simple synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websocket_streaming_basic():
    """Test WebSocket streaming with basic configuration"""
    print("\nTesting WebSocket streaming (basic)...")
    print("=" * 60)
    
    try:
        async with websockets.connect(TTS_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send text for synthesis
            test_text = TEST_TEXTS["medium"]
            
            print(f"\n📝 Sending text ({len(test_text)} chars):")
            print(f"   \"{test_text[:100]}...\"")
            
            await websocket.send(json.dumps({
                "type": "text",
                "text": test_text
            }))
            
            # Receive messages
            audio_chunks = []
            messages_received = 0
            start_time = time.time()
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    messages_received += 1
                    
                    if isinstance(message, bytes):
                        # Audio data
                        audio_chunks.append(message)
                        print(f"   [Received audio chunk {len(audio_chunks)}: {len(message)} bytes]", end='\r')
                    else:
                        # JSON message
                        data = json.loads(message)
                        msg_type = data.get('type')
                        
                        if msg_type == "synthesis_start":
                            print(f"\n🎤 Synthesis started: {data.get('char_count')} chars")
                            
                        elif msg_type == "audio_complete":
                            print(f"\n✅ Audio complete!")
                            processing_time = time.time() - start_time
                            print(f"   Total time: {processing_time:.3f}s")
                            print(f"   Audio chunks: {len(audio_chunks)}")
                            break
                            
                        elif msg_type == "error":
                            print(f"\n✗ Error: {data.get('message')}")
                            return False
                            
                except asyncio.TimeoutError:
                    print("\n⚠️ Timeout waiting for response")
                    break
            
            # Save combined audio
            if audio_chunks:
                combined_audio = b''.join(audio_chunks)
                print(f"   Total audio: {len(combined_audio):,} bytes")
                save_audio(combined_audio, "test_output_ws_basic.wav")
            
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"✗ WebSocket basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websocket_streaming_custom_config():
    """Test WebSocket streaming with custom configuration"""
    print("\nTesting WebSocket streaming (custom config)...")
    print("=" * 60)
    
    # Custom configuration - ElevenLabs style
    custom_config = {
        "type": "config",
        "audio": {
            "sample_rate": 24000,
            "channels": 1,
            "encoding": "pcm_s16le"
        },
        "voice": {
            "speaker": "default",
            "speed": 1.2,  # Faster speech
            "pitch": 1.0,
            "energy": 1.1
        },
        "streaming": {
            "enabled": True,
            "chunk_size": 1024,
            "flush_threshold": 2,  # Flush after 2 sentences
            "optimize_streaming_latency": 3,  # Fast
            "sentence_silence_duration": 0.2
        },
        "synthesis": {
            "stability": 0.6,
            "similarity_boost": 0.8,
            "temperature": 0.8
        },
        "text_processing": {
            "normalize_text": True,
            "split_sentences": True
        }
    }
    
    try:
        async with websockets.connect(TTS_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send custom configuration
            print("\n📋 Sending custom configuration:")
            print(f"   Speed: {custom_config['voice']['speed']}x")
            print(f"   Flush threshold: {custom_config['streaming']['flush_threshold']} sentences")
            print(f"   Latency optimization: {custom_config['streaming']['optimize_streaming_latency']}")
            
            await websocket.send(json.dumps(custom_config))
            
            # Wait for ready confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'ready':
                print(f"✓ {data.get('message')}")
            else:
                print(f"✗ Unexpected response: {data}")
                return False
            
            # Send text
            test_text = TEST_TEXTS["multi_sentence"]
            
            print(f"\n📝 Sending text ({len(test_text)} chars):")
            print(f"   \"{test_text}\"")
            
            await websocket.send(json.dumps({
                "type": "text",
                "text": test_text
            }))
            
            # Force flush to get all audio
            await asyncio.sleep(0.5)
            await websocket.send(json.dumps({"type": "flush"}))
            
            # Receive messages
            audio_chunks = []
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    
                    if isinstance(message, bytes):
                        audio_chunks.append(message)
                        print(f"   [Audio chunk {len(audio_chunks)}]", end='\r')
                    else:
                        data = json.loads(message)
                        msg_type = data.get('type')
                        
                        if msg_type == "flush_complete":
                            print(f"\n✅ Flush complete!")
                            break
                        elif msg_type == "audio_complete":
                            print(f"\n✅ Audio segment complete")
                            
                except asyncio.TimeoutError:
                    break
            
            # Save audio
            if audio_chunks:
                combined_audio = b''.join(audio_chunks)
                print(f"   Total audio: {len(combined_audio):,} bytes ({len(audio_chunks)} chunks)")
                save_audio(combined_audio, "test_output_ws_custom.wav")
            
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"✗ WebSocket custom config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_control_messages():
    """Test control messages (flush, reset, get_stats)"""
    print("\nTesting control messages...")
    print("=" * 60)
    
    try:
        async with websockets.connect(TTS_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send some text
            print("\n  📤 Sending text...")
            await websocket.send(json.dumps({
                "type": "text",
                "text": TEST_TEXTS["short"]
            }))
            
            await asyncio.sleep(0.3)
            
            # Test get_stats
            print("\n  ⚙️  Testing get_stats...")
            await websocket.send(json.dumps({"type": "get_stats"}))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            stats = json.loads(response)
            if stats.get('type') == 'stats':
                print(f"  ✓ Stats received:")
                print(f"     Total chars: {stats.get('total_chars_processed')}")
                print(f"     Buffered sentences: {stats.get('buffered_sentences')}")
            
            # Test reset
            print("\n  🔄 Testing reset...")
            await websocket.send(json.dumps({"type": "reset"}))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            reset_resp = json.loads(response)
            if reset_resp.get('type') == 'status':
                print(f"  ✓ {reset_resp.get('message')}")
            
            # Test flush
            print("\n  💾 Testing flush...")
            await websocket.send(json.dumps({
                "type": "text",
                "text": "Another test sentence."
            }))
            
            await asyncio.sleep(0.2)
            await websocket.send(json.dumps({"type": "flush"}))
            
            # Collect responses
            messages = []
            try:
                for _ in range(10):
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    if isinstance(msg, str):
                        data = json.loads(msg)
                        messages.append(data)
                        if data.get('type') == 'flush_complete':
                            print(f"  ✓ Flush completed")
                            break
            except asyncio.TimeoutError:
                pass
            
            print(f"\n✓ Control messages test complete ({len(messages)} responses)")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"✗ Control messages test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_latency():
    """Test streaming latency with incremental text"""
    print("\nTesting streaming latency...")
    print("=" * 60)
    
    try:
        async with websockets.connect(TTS_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Configure for low latency
            config = {
                "type": "config",
                "streaming": {
                    "enabled": True,
                    "flush_threshold": 1,  # Flush after each sentence
                    "optimize_streaming_latency": 4  # Maximum speed
                }
            }
            
            await websocket.send(json.dumps(config))
            response = await websocket.recv()
            print("✓ Configured for low latency")
            
            # Send sentences incrementally
            sentences = TEST_TEXTS["multi_sentence"].split(". ")
            
            print(f"\n📝 Sending {len(sentences)} sentences incrementally...")
            
            for i, sentence in enumerate(sentences, 1):
                if not sentence.endswith("."):
                    sentence += "."
                
                print(f"\n  [{i}/{len(sentences)}] Sending: \"{sentence}\"")
                send_time = time.time()
                
                await websocket.send(json.dumps({
                    "type": "text",
                    "text": sentence
                }))
                
                # Wait for first audio chunk
                first_chunk_time = None
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        
                        if isinstance(message, bytes) and first_chunk_time is None:
                            first_chunk_time = time.time()
                            latency = first_chunk_time - send_time
                            print(f"    ⚡ First audio chunk latency: {latency*1000:.0f}ms")
                            break
                        elif isinstance(message, str):
                            data = json.loads(message)
                            if data.get('type') == 'audio_complete':
                                break
                                
                    except asyncio.TimeoutError:
                        print(f"    ⚠️ Timeout")
                        break
                
                await asyncio.sleep(0.1)
            
            print("\n=" * 60)
            return True
            
    except Exception as e:
        print(f"✗ Latency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 70)
    print("CosyVoice2 TTS Service - Test Suite v1.0")
    print("Comprehensive API Testing")
    print("=" * 70)
    
    results = []
    
    # Test 1: Health check
    print("\n[1/8] Health Check")
    results.append(("Health Check", test_health()))
    
    # Test 2: Get default config
    print("\n[2/8] Default Configuration")
    results.append(("Get Default Config", test_get_default_config()))
    
    # Test 3: List voices
    print("\n[3/8] List Voices")
    results.append(("List Voices", test_list_voices()))
    
    # Test 4: Simple HTTP synthesis
    print("\n[4/8] HTTP Synthesis")
    results.append(("HTTP Synthesis", test_simple_synthesis()))
    
    # Test 5: WebSocket streaming (basic)
    print("\n[5/8] WebSocket Streaming (Basic)")
    results.append(("WebSocket Basic", await test_websocket_streaming_basic()))
    
    # Test 6: WebSocket streaming (custom config)
    print("\n[6/8] WebSocket Streaming (Custom Config)")
    results.append(("WebSocket Custom", await test_websocket_streaming_custom_config()))
    
    # Test 7: Control messages
    print("\n[7/8] Control Messages")
    results.append(("Control Messages", await test_control_messages()))
    
    # Test 8: Streaming latency
    print("\n[8/8] Streaming Latency")
    results.append(("Streaming Latency", await test_streaming_latency()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n{'✓' if passed == total else '✗'} Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    # List generated files
    print("\n📁 Generated test files:")
    for file in Path(".").glob("test_output_*.wav"):
        size = file.stat().st_size
        print(f"   - {file.name} ({size:,} bytes)")
    print()
    
    return all(p for _, p in results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

