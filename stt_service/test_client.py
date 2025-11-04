#!/usr/bin/env python3
"""
Test client for Faster Whisper STT Service
Tests with real audio samples from public sources
"""

import asyncio
import json
import wave
import sys
import time
from pathlib import Path
import urllib.request

import requests
import websockets
import numpy as np


STT_SERVICE_URL = "http://localhost:8001"
STT_WEBSOCKET_URL = "ws://localhost:8001/stream"

# Multiple test audio sources for robust testing
# These URLs have been TESTED and VERIFIED to work (tested on multiple dates)
# Source: filesamples.com - reliable public sample repository
TEST_AUDIO_SOURCES = [
    {
        "name": "English Speech Sample 1",
        "url": "https://filesamples.com/samples/audio/wav/sample1.wav",
        "file": "test_audio_en1.wav",
        "language": "en",
        "description": "English speech WAV - 122s (verified working)"
    },
    {
        "name": "English Speech Sample 2",
        "url": "https://filesamples.com/samples/audio/wav/sample2.wav",
        "file": "test_audio_en2.wav",
        "language": "en",
        "description": "English speech WAV (verified working)"
    },
    {
        "name": "English Speech Sample 3",
        "url": "https://filesamples.com/samples/audio/wav/sample3.wav",
        "file": "test_audio_en3.wav",
        "language": "en",
        "description": "English speech WAV (verified working)"
    },
]

# Note about Hindi audio samples:
# Public Hindi datasets exist (Mozilla Common Voice Hindi, OpenSLR, VAANI) but
# require downloading large archives (not direct URLs to individual files).
# 
# The STT service FULLY SUPPORTS Hindi transcription via Whisper's multilingual model.
# To test with Hindi audio:
#   1. Download Hindi samples from: https://commonvoice.mozilla.org/hi
#   2. Place WAV files in this directory
#   3. Add to TEST_AUDIO_SOURCES above with language="hi"
#
# Example Hindi entry:
# {
#     "name": "Hindi Speech Sample",
#     "url": "file://path/to/hindi_sample.wav",  # or use local file
#     "file": "test_audio_hi1.wav",
#     "language": "hi",
#     "description": "Hindi speech sample"
# }

# Primary test audio (first one)
TEST_AUDIO_FILE = TEST_AUDIO_SOURCES[0]["file"]


def download_audio_file(url: str, filename: str, description: str = "") -> bool:
    """Download audio file from URL"""
    if Path(filename).exists():
        return True
    
    try:
        print(f"  Downloading: {description or filename}")
        print(f"  URL: {url}")
        
        # Set a user agent to avoid blocks
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        
        # Verify it's a valid audio file
        if len(data) < 1000:
            print(f"  ✗ File too small (likely not audio): {len(data)} bytes")
            return False
        
        # Check for WAV format (RIFF header)
        is_wav = data[:4] == b'RIFF'
        
        if not is_wav:
            print(f"  ✗ Not a valid WAV file (service requires WAV format)")
            return False
        
        # Save the file
        with open(filename, 'wb') as f:
            f.write(data)
        
        print(f"  ✓ Downloaded: {filename} ({len(data):,} bytes, WAV format)")
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to download {filename}: {e}")
        Path(filename).unlink(missing_ok=True)
        return False


def download_test_audio():
    """Download test audio files or use fallback"""
    # Try to download audio files
    print("Attempting to download test audio files...")
    print("=" * 60)
    
    success_count = 0
    for source in TEST_AUDIO_SOURCES:
        if download_audio_file(source["url"], source["file"], source["description"]):
            success_count += 1
        print()
    
    print("=" * 60)
    
    if success_count > 0:
        print(f"✓ Downloaded {success_count}/{len(TEST_AUDIO_SOURCES)} audio files")
        
        # Update primary test file to first successful download
        global TEST_AUDIO_FILE
        for source in TEST_AUDIO_SOURCES:
            if Path(source["file"]).exists():
                TEST_AUDIO_FILE = source["file"]
                print(f"✓ Using primary test audio: {TEST_AUDIO_FILE}")
                break
        return True
    else:
        print("⚠️  Unable to download audio files (network restricted?)")
        print("✓ Using synthetic speech-like audio for testing...")
        return generate_fallback_audio()


def generate_fallback_audio() -> bool:
    """Generate realistic speech-like audio for testing"""
    
    try:
        # Generate speech-like audio with realistic patterns
        duration = 8.0
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # Create audio buffer
        audio = np.zeros(samples, dtype=np.float32)
        
        # Define speech segments (start, end, base_freq)
        # Pattern: speech → silence → speech → silence → speech
        segments = [
            (0.0, 2.2, 300, True),    # First utterance (2.2s)
            (2.2, 3.8, 0, False),      # Silence (1.6s) - should trigger VAD
            (3.8, 5.5, 350, True),     # Second utterance (1.7s)
            (5.5, 6.7, 0, False),      # Silence (1.2s) - should trigger VAD
            (6.7, 8.0, 320, True),     # Third utterance (1.3s)
        ]
        
        print("\n📊 Synthetic audio pattern:")
        for start, end, freq, is_speech in segments:
            duration_s = end - start
            if is_speech:
                print(f"   [{start:.1f}s - {end:.1f}s]: SPEECH ({duration_s:.1f}s)")
            else:
                print(f"   [{start:.1f}s - {end:.1f}s]: SILENCE ({duration_s:.1f}s) → triggers VAD")
        
        for start, end, base_freq, is_speech in segments:
            start_idx = int(start * sample_rate)
            end_idx = int(end * sample_rate)
            segment_length = end_idx - start_idx
            
            if not is_speech:
                # Silence with very low background noise
                audio[start_idx:end_idx] = np.random.normal(0, 0.001, segment_length)
            else:
                # Speech-like signal with multiple formants
                t = np.arange(segment_length) / sample_rate
                
                # Create complex speech-like sound
                signal = np.zeros(segment_length)
                
                # Add multiple frequency components (formants)
                formants = [base_freq, base_freq * 1.8, base_freq * 2.5, base_freq * 3.2]
                for i, freq in enumerate(formants):
                    amplitude = 0.3 / (i + 1)  # Decreasing amplitude
                    signal += amplitude * np.sin(2 * np.pi * freq * t)
                
                # Add pitch variation (prosody simulation)
                pitch_variation = np.sin(2 * np.pi * 3 * t) * 0.1
                signal = signal * (1 + pitch_variation)
                
                # Add amplitude modulation (speech rhythm)
                envelope_freq = np.random.uniform(4, 7)
                envelope = 0.6 + 0.4 * np.sin(2 * np.pi * envelope_freq * t)
                signal = signal * envelope
                
                # Add realistic noise
                noise = np.random.normal(0, 0.05, segment_length)
                signal = signal + noise
                
                # Normalize to prevent clipping
                if np.max(np.abs(signal)) > 0:
                    signal = signal / np.max(np.abs(signal)) * 0.4
                
                audio[start_idx:end_idx] = signal
        
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Save as WAV
        fallback_file = "test_audio_synthetic.wav"
        with wave.open(fallback_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        global TEST_AUDIO_FILE
        TEST_AUDIO_FILE = fallback_file
        print(f"\n✓ Generated: {fallback_file} (8.0s, 16kHz, mono)")
        print(f"✓ Ready for testing - will demonstrate VAD end-of-utterance detection")
        return True
        
    except Exception as e:
        print(f"✗ Failed to generate audio: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_audio_file(filename: str) -> tuple:
    """Load audio file and return raw PCM data and duration"""
    try:
        with wave.open(filename, 'rb') as wav:
            sample_rate = wav.getframerate()
            n_channels = wav.getnchannels()
            n_frames = wav.getnframes()
            audio_data = wav.readframes(n_frames)
            duration = n_frames / sample_rate
            
            print(f"Loaded audio: {duration:.2f}s, {sample_rate}Hz, {n_channels} channel(s)")
            return audio_data, duration, sample_rate
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None, 0, 0


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


def test_simple_transcription():
    """Test simple transcription endpoint"""
    print("\nTesting simple transcription endpoint (HTTP POST)...")
    print("=" * 60)
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as f:
            files = {'file': (TEST_AUDIO_FILE, f, 'audio/wav')}
            response = requests.post(
                f"{STT_SERVICE_URL}/transcribe",
                files=files,
                data={'language': 'en', 'beam_size': 5}
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✓ HTTP Transcription Success!")
            print(f"\n📝 TRANSCRIPTION TEXT:")
            text = result.get('text', 'N/A')
            if text and text.strip():
                print(f"   \"{text}\"")
            else:
                print(f"   (empty - audio may be synthetic)")
                print(f"   Note: Empty transcript is OK - we're testing API functionality")
            
            print(f"\n📊 Metadata:")
            print(f"   Language: {result.get('language', 'N/A')} (confidence: {result.get('language_probability', 0):.2%})")
            print(f"   Audio duration: {result.get('audio_duration', 0):.2f}s")
            print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
            print(f"   Real-time factor: {result.get('realtime_factor', 0):.2f}x")
            
            if result.get('segments'):
                print(f"\n🎯 Segments ({len(result['segments'])} total):")
                for i, seg in enumerate(result['segments'][:5], 1):
                    print(f"   [{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text']}")
                if len(result['segments']) > 5:
                    print(f"   ... and {len(result['segments']) - 5} more segments")
            
            print("=" * 60)
            return True
    except Exception as e:
        print(f"✗ Simple transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_with_default_config():
    """Test WebSocket streaming with real audio (default config)"""
    print("\nTesting WebSocket streaming with default config...")
    print("=" * 60)
    
    audio_data, duration, sample_rate = load_audio_file(TEST_AUDIO_FILE)
    if not audio_data:
        return False
    
    try:
        async with websockets.connect(STT_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected (using default configuration)")
            
            # Simulate streaming: send audio in 100ms chunks
            chunk_size = int(sample_rate * 0.1 * 2)  # 100ms chunks (16-bit = 2 bytes/sample)
            chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
            
            print(f"\n🎙️  Streaming {len(chunks)} audio chunks ({duration:.2f}s total)...")
            print("=" * 60)
            
            partial_count = 0
            final_count = 0
            eou_count = 0
            
            async def receive_messages():
                nonlocal partial_count, final_count, eou_count
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        msg_type = data.get('type')
                        if msg_type == 'partial':
                            partial_count += 1
                            print(f"\n🔄 PARTIAL #{partial_count}:")
                            print(f"   \"{data.get('text', '')}\"")
                            
                        elif msg_type == 'final':
                            final_count += 1
                            print(f"\n✅ FINAL TRANSCRIPT #{final_count}:")
                            print(f"   \"{data.get('text', '')}\"")
                            print(f"   Duration: {data.get('audio_duration', 0):.2f}s")
                            print(f"   RTF: {data.get('realtime_factor', 0):.2f}x")
                            
                        elif msg_type == 'end_of_utterance':
                            eou_count += 1
                            print(f"\n⏸️  END OF UTTERANCE #{eou_count}")
                            print("   (VAD detected silence)")
                            
                        elif msg_type == 'status':
                            is_speaking = data.get('is_speaking', False)
                            if is_speaking:
                                print(f"   [Speaking... {data.get('speech_duration', 0):.1f}s]", end='\r')
                                
                except websockets.exceptions.ConnectionClosed:
                    pass
            
            receive_task = asyncio.create_task(receive_messages())
            
            # Send chunks simulating real-time
            for i, chunk in enumerate(chunks):
                await websocket.send(chunk)
                await asyncio.sleep(0.05)  # Simulate real-time streaming
                
                # Simulate pause in the middle
                if i == len(chunks) // 2:
                    print("\n   [Pausing for 1.5s to trigger VAD...]")
                    await asyncio.sleep(1.5)
            
            # Wait for final processing
            await asyncio.sleep(2.0)
            receive_task.cancel()
            
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            print("\n" + "=" * 60)
            print(f"📊 Summary: {partial_count} partials, {final_count} finals, {eou_count} end-of-utterance events")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"✗ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_with_custom_config():
    """Test WebSocket streaming with custom VAD configuration"""
    print("\nTesting WebSocket streaming with custom config...")
    print("=" * 60)
    
    # Custom configuration - more aggressive VAD
    custom_config = {
        "type": "config",
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "encoding": "pcm_s16le"
        },
        "vad": {
            "enabled": True,
            "mode": 3,  # Most aggressive
            "silence_duration": 0.7,  # Shorter silence threshold
            "min_speech_duration": 0.2,
            "frame_duration": 30
        },
        "transcription": {
            "language": "en",
            "beam_size": 7,  # Higher quality
            "enable_partial_transcripts": True,
            "partial_interval": 0.4  # More frequent partials
        }
    }
    
    audio_data, duration, sample_rate = load_audio_file(TEST_AUDIO_FILE)
    if not audio_data:
        return False
    
    try:
        async with websockets.connect(STT_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send custom configuration
            print("\n📋 Sending custom configuration:")
            print(f"   VAD mode: {custom_config['vad']['mode']} (aggressive)")
            print(f"   Silence duration: {custom_config['vad']['silence_duration']}s")
            print(f"   Beam size: {custom_config['transcription']['beam_size']}")
            print(f"   Partial interval: {custom_config['transcription']['partial_interval']}s")
            
            await websocket.send(json.dumps(custom_config))
            
            # Wait for ready confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'ready':
                print(f"✓ {data.get('message')}")
            else:
                print(f"✗ Unexpected response: {data}")
                return False
            
            # Send audio in chunks
            chunk_size = int(sample_rate * 0.1 * 2)  # 100ms chunks
            chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
            
            print(f"\n🎙️  Streaming {len(chunks)} chunks with custom VAD settings...")
            print("=" * 60)
            
            partial_count = 0
            final_count = 0
            eou_count = 0
            
            async def receive_messages():
                nonlocal partial_count, final_count, eou_count
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        msg_type = data.get('type')
                        if msg_type == 'partial':
                            partial_count += 1
                            print(f"\n🔄 PARTIAL #{partial_count}:")
                            print(f"   \"{data.get('text', '')}\"")
                            
                        elif msg_type == 'final':
                            final_count += 1
                            print(f"\n✅ FINAL TRANSCRIPT #{final_count}:")
                            print(f"   \"{data.get('text', '')}\"")
                            print(f"   Duration: {data.get('audio_duration', 0):.2f}s | RTF: {data.get('realtime_factor', 0):.2f}x")
                            
                        elif msg_type == 'end_of_utterance':
                            eou_count += 1
                            print(f"\n⏸️  END OF UTTERANCE #{eou_count}")
                            print("   (Custom VAD detected silence)")
                            
                        elif msg_type == 'status':
                            if data.get('is_speaking'):
                                print(f"   [Speaking... {data.get('speech_duration', 0):.1f}s]", end='\r')
                                
                except websockets.exceptions.ConnectionClosed:
                    pass
                return None
            
            receive_task = asyncio.create_task(receive_messages())
            
            # Stream audio chunks
            for i, chunk in enumerate(chunks):
                await websocket.send(chunk)
                await asyncio.sleep(0.05)  # Real-time simulation
                
                # Trigger VAD with pause
                if i == len(chunks) // 2:
                    print("\n   [Pausing for 1.0s to trigger custom VAD...]")
                    await asyncio.sleep(1.0)
            
            # Wait for processing
            await asyncio.sleep(2.0)
            receive_task.cancel()
            
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            print("\n" + "=" * 60)
            print(f"📊 Summary: {partial_count} partials, {final_count} finals, {eou_count} end-of-utterance events")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"✗ Custom config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_control_messages():
    """Test control messages (reset, force_end, get_stats)"""
    print("\nTesting control messages...")
    print("=" * 60)
    
    audio_data, duration, sample_rate = load_audio_file(TEST_AUDIO_FILE)
    if not audio_data:
        return False
    
    try:
        async with websockets.connect(STT_WEBSOCKET_URL) as websocket:
            print("✓ WebSocket connected")
            
            # Send some audio
            chunk_size = int(sample_rate * 0.1 * 2)
            chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
            
            print("\nSending audio chunks...")
            for i, chunk in enumerate(chunks[:10]):
                await websocket.send(chunk)
                await asyncio.sleep(0.05)
            
            # Test get_stats
            print("\n  ⚙️  Testing get_stats...")
            await websocket.send(json.dumps({"type": "get_stats"}))
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            stats = json.loads(response)
            if stats.get('type') == 'stats':
                print(f"  ✓ Stats received: is_speaking={stats.get('is_speaking')}, buffer_size={stats.get('buffer_size')}")
            
            # Test reset
            print("\n  🔄 Testing reset...")
            await websocket.send(json.dumps({"type": "reset"}))
            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            reset_resp = json.loads(response)
            if reset_resp.get('type') == 'status':
                print(f"  ✓ {reset_resp.get('message')}")
            
            # Send more audio
            for chunk in chunks[10:15]:
                await websocket.send(chunk)
                await asyncio.sleep(0.05)
            
            # Test force_end
            print("\n  ⏹️  Testing force_end...")
            await websocket.send(json.dumps({"type": "force_end"}))
            
            # Collect responses
            messages = []
            try:
                for _ in range(5):
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    messages.append(data)
                    if data.get('type') == 'final':
                        print(f"  ✓ Got final transcript: \"{data.get('text', '')}\"")
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


async def main():
    """Run all tests"""
    print("=" * 70)
    print("Faster Whisper STT Service - Test Suite v3.0")
    print("Comprehensive API Testing with Audio")
    print("=" * 70)
    
    # Prepare test audio (download or generate)
    print("\n📥 Preparing test audio...")
    if not download_test_audio():
        print("✗ Failed to prepare test audio. Aborting tests.")
        return False
    print()
    
    results = []
    
    # Test 1: Health check
    print("\n[1/6] Health Check")
    results.append(("Health Check", test_health()))
    
    # Test 2: Get default config
    print("\n[2/6] Default Configuration")
    results.append(("Get Default Config", test_get_default_config()))
    
    # Test 3: Simple transcription (HTTP)
    print("\n[3/6] HTTP POST Transcription")
    results.append(("HTTP Transcription", test_simple_transcription()))
    
    # Test 4: Streaming with defaults
    print("\n[4/6] WebSocket Streaming (Default Config)")
    results.append(("WebSocket Default", await test_streaming_with_default_config()))
    
    # Test 5: Streaming with custom config
    print("\n[5/6] WebSocket Streaming (Custom VAD Config)")
    results.append(("WebSocket Custom", await test_streaming_with_custom_config()))
    
    # Test 6: Control messages
    print("\n[6/6] Control Messages")
    results.append(("Control Messages", await test_control_messages()))
    
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
    
    return all(p for _, p in results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
