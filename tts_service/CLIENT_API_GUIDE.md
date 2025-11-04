# TTS Service - Client API Guide

Complete API reference for the CosyVoice2 TTS Service with production-ready examples.

## 📋 Table of Contents

1. [Overview](#overview)
2. [HTTP REST API](#http-rest-api)
3. [WebSocket Streaming API](#websocket-streaming-api)
4. [Configuration Guide](#configuration-guide)
5. [Code Examples](#code-examples)
6. [Best Practices](#best-practices)
7. [Error Handling](#error-handling)

---

## Overview

### Service Information

- **Base URL**: `http://localhost:8002`
- **WebSocket URL**: `ws://localhost:8002/stream`
- **Default Port**: 8002
- **Protocol**: HTTP/1.1, WebSocket
- **Content-Type**: application/json

### Quick Reference

| Feature | HTTP Endpoint | WebSocket Event |
|---------|---------------|-----------------|
| Health Check | `GET /health` | N/A |
| List Voices | `GET /voices` | N/A |
| Simple Synthesis | `POST /synthesize` | N/A |
| Streaming Synthesis | `POST /synthesize/stream` | `type: text` |
| Configuration | `GET /config/defaults` | `type: config` |

---

## HTTP REST API

### 1. Health Check

Check service status and model information.

**Endpoint**: `GET /health`

**Request**:
```bash
curl http://localhost:8002/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "CosyVoice2 TTS",
  "model_name": "CosyVoice2-0.5B",
  "model_path": "FunAudioLLM/CosyVoice2-0.5B",
  "device": "cuda",
  "available_speakers": [
    "default",
    "female_calm",
    "male_energetic",
    "female_friendly",
    "male_professional"
  ],
  "mode": "cosyvoice"
}
```

**Python Example**:
```python
import requests

response = requests.get('http://localhost:8002/health')
health = response.json()

print(f"Status: {health['status']}")
print(f"Device: {health['device']}")
print(f"Available speakers: {len(health['available_speakers'])}")
```

---

### 2. Get Default Configuration

Retrieve default configuration values.

**Endpoint**: `GET /config/defaults`

**Request**:
```bash
curl http://localhost:8002/config/defaults
```

**Response** (200 OK):
```json
{
  "audio": {
    "sample_rate": 24000,
    "channels": 1,
    "encoding": "pcm_s16le",
    "bitrate": 128
  },
  "voice": {
    "speaker": "default",
    "style": null,
    "speed": 1.0,
    "pitch": 1.0,
    "energy": 1.0
  },
  "streaming": {
    "enabled": true,
    "chunk_size": 1024,
    "flush_threshold": 3,
    "optimize_streaming_latency": 2,
    "enable_ssml_parsing": false,
    "buffer_size": 3,
    "sentence_silence_duration": 0.3
  },
  "synthesis": {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "use_speaker_boost": true,
    "temperature": 0.7,
    "top_k": 50,
    "top_p": 0.9,
    "repetition_penalty": 1.0,
    "max_new_tokens": 2048
  },
  "text_processing": {
    "normalize_text": true,
    "split_sentences": true,
    "remove_special_chars": false,
    "max_sentence_length": 500
  }
}
```

**Python Example**:
```python
import requests

response = requests.get('http://localhost:8002/config/defaults')
config = response.json()

# Use as template for custom configuration
custom_config = config.copy()
custom_config['voice']['speed'] = 1.2
custom_config['streaming']['flush_threshold'] = 2
```

---

### 3. List Available Voices

Get all available voice speakers.

**Endpoint**: `GET /voices`

**Request**:
```bash
curl http://localhost:8002/voices
```

**Response** (200 OK):
```json
{
  "voices": [
    {
      "id": "default",
      "name": "Default",
      "language": "multi",
      "gender": "neutral"
    },
    {
      "id": "female_calm",
      "name": "Female Calm",
      "language": "multi",
      "gender": "female"
    },
    {
      "id": "male_energetic",
      "name": "Male Energetic",
      "language": "multi",
      "gender": "male"
    }
  ],
  "count": 3
}
```

**Python Example**:
```python
import requests

response = requests.get('http://localhost:8002/voices')
voices = response.json()['voices']

for voice in voices:
    print(f"{voice['id']}: {voice['name']} ({voice['gender']})")
```

---

### 4. Synthesize Text (Simple)

Synthesize text to speech with optional configuration.

**Endpoint**: `POST /synthesize`

**Request Body**:
```json
{
  "text": "Hello, this is a test of the text-to-speech service!",
  "voice_config": {
    "speaker": "default",
    "speed": 1.0,
    "pitch": 1.0,
    "energy": 1.0
  },
  "audio_config": {
    "sample_rate": 24000,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "synthesis_config": {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "temperature": 0.7
  }
}
```

**Note**: All config fields are optional. Service uses defaults if not provided.

**Response** (200 OK):
```json
{
  "success": true,
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABA...",
  "audio_format": "pcm_s16le",
  "text": "Hello, this is a test...",
  "sample_rate": 24000,
  "audio_duration": 3.2,
  "processing_time": 0.156,
  "realtime_factor": 0.049,
  "speaker": "default"
}
```

**Python Example - Basic**:
```python
import requests
import base64
import wave

response = requests.post('http://localhost:8002/synthesize', json={
    "text": "Hello! This is a test of the text-to-speech service."
})

result = response.json()

# Decode audio
audio_bytes = base64.b64decode(result['audio_base64'])

# Save to WAV file
with wave.open('output.wav', 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(result['sample_rate'])
    wav_file.writeframes(audio_bytes)

print(f"✓ Synthesized {result['audio_duration']:.2f}s of audio")
print(f"  Processing time: {result['processing_time']:.3f}s")
print(f"  Real-time factor: {result['realtime_factor']:.2f}x")
```

**Python Example - With Configuration**:
```python
import requests
import base64
import wave

response = requests.post('http://localhost:8002/synthesize', json={
    "text": "This is faster speech with higher pitch.",
    "voice_config": {
        "speaker": "female_calm",
        "speed": 1.3,      # 30% faster
        "pitch": 1.1,      # 10% higher
        "energy": 1.0
    },
    "synthesis_config": {
        "stability": 0.7,           # More stable/consistent
        "similarity_boost": 0.8,    # More similar to target voice
        "temperature": 0.6          # Less random
    }
})

result = response.json()
audio_bytes = base64.b64decode(result['audio_base64'])

# Save audio...
with wave.open('output_custom.wav', 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(result['sample_rate'])
    wav_file.writeframes(audio_bytes)
```

**curl Example**:
```bash
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "voice_config": {
      "speaker": "default",
      "speed": 1.0
    }
  }' | jq '.audio_duration'
```

---

### 5. Streaming Synthesis (HTTP)

Synthesize text with streaming HTTP response.

**Endpoint**: `POST /synthesize/stream`

**Request Body**: Same as `/synthesize`

**Response**: Streaming audio data (Content-Type: audio/pcm_s16le or configured format)

**Python Example**:
```python
import requests

response = requests.post(
    'http://localhost:8002/synthesize/stream',
    json={
        "text": "This is streaming synthesis over HTTP!",
        "voice_config": {"speed": 1.0}
    },
    stream=True  # Important!
)

# Process audio chunks as they arrive
with open('output_stream.wav', 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
            # Can play audio in real-time here

print("✓ Streaming synthesis complete")
```

---

## WebSocket Streaming API

### Connection

**URL**: `ws://localhost:8002/stream`

**Protocol**: WebSocket (RFC 6455)

### Message Types

#### Client → Server

1. **Configuration Message** (optional, once at start):
```json
{
  "type": "config",
  "audio": { ... },
  "voice": { ... },
  "streaming": { ... },
  "synthesis": { ... },
  "text_processing": { ... }
}
```

2. **Text Message** (synthesize text):
```json
{
  "type": "text",
  "text": "Text to synthesize"
}
```

3. **Control Messages**:
```json
{"type": "flush"}      // Force flush buffered text
{"type": "reset"}      // Reset text buffer
{"type": "get_stats"}  // Get session statistics
```

#### Server → Client

1. **Ready** (after configuration):
```json
{
  "type": "ready",
  "message": "Session configured and ready",
  "config": { ... }
}
```

2. **Session Started**:
```json
{
  "type": "session_started",
  "message": "Streaming session ready"
}
```

3. **Synthesis Start**:
```json
{
  "type": "synthesis_start",
  "text": "Text being synthesized",
  "char_count": 42
}
```

4. **Audio Data** (binary):
```
[Binary audio bytes in configured format]
```

5. **Audio Complete**:
```json
{
  "type": "audio_complete",
  "text": "Synthesized text",
  "chunks_sent": 15,
  "processing_time": 0.234
}
```

6. **Flush Complete**:
```json
{
  "type": "flush_complete",
  "message": "All buffered text synthesized"
}
```

7. **Statistics**:
```json
{
  "type": "stats",
  "total_chars_processed": 150,
  "total_audio_duration": 12.5,
  "buffered_sentences": 2,
  "total_processed": 5,
  "will_flush_in": 1
}
```

8. **Error**:
```json
{
  "type": "error",
  "message": "Error description"
}
```

### WebSocket Flow

```
Client                          Server
  |                               |
  |---- Connect WebSocket ------->|
  |<---- Accept Connection -------|
  |                               |
  |---- Config Message (opt) ---->|
  |<---- Ready Message ----------|
  |                               |
  |---- Text Message ------------>|
  |<---- Synthesis Start ---------|
  |<---- Audio Chunk (binary) ---|
  |<---- Audio Chunk (binary) ---|
  |<---- Audio Chunk (binary) ---|
  |<---- Audio Complete ----------|
  |                               |
  |---- Text Message ------------>|
  |<---- Synthesis Start ---------|
  |<---- Audio Chunks... ---------|
  |                               |
  |---- Flush Message ----------->|
  |<---- Audio Chunks... ---------|
  |<---- Flush Complete ----------|
  |                               |
  |---- Close Connection -------->|
```

---

### WebSocket Examples

#### Example 1: Basic Streaming

```python
import asyncio
import websockets
import json

async def basic_streaming():
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        print("✓ Connected")
        
        # Send text
        await ws.send(json.dumps({
            "type": "text",
            "text": "Hello! This is a streaming test."
        }))
        
        # Receive audio
        audio_chunks = []
        while True:
            message = await ws.recv()
            
            if isinstance(message, bytes):
                # Audio data
                audio_chunks.append(message)
                print(f"Received chunk: {len(message)} bytes")
            else:
                # JSON message
                data = json.loads(message)
                print(f"Message: {data['type']}")
                
                if data['type'] == 'audio_complete':
                    break
        
        print(f"✓ Complete! Received {len(audio_chunks)} chunks")

asyncio.run(basic_streaming())
```

#### Example 2: With Custom Configuration

```python
import asyncio
import websockets
import json
import wave

async def configured_streaming():
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Send configuration
        config = {
            "type": "config",
            "audio": {
                "sample_rate": 24000,
                "encoding": "pcm_s16le"
            },
            "voice": {
                "speaker": "female_calm",
                "speed": 1.2,
                "pitch": 1.0
            },
            "streaming": {
                "flush_threshold": 2,
                "optimize_streaming_latency": 3
            },
            "synthesis": {
                "stability": 0.6,
                "temperature": 0.7
            }
        }
        
        await ws.send(json.dumps(config))
        
        # Wait for ready
        response = await ws.recv()
        ready = json.loads(response)
        assert ready['type'] == 'ready'
        print("✓ Configured")
        
        # Send text
        await ws.send(json.dumps({
            "type": "text",
            "text": "This is using custom configuration!"
        }))
        
        # Receive and save audio
        audio_chunks = []
        sample_rate = 24000
        
        while True:
            message = await ws.recv()
            
            if isinstance(message, bytes):
                audio_chunks.append(message)
            else:
                data = json.loads(message)
                if data['type'] == 'audio_complete':
                    break
        
        # Save to file
        combined_audio = b''.join(audio_chunks)
        with wave.open('output_configured.wav', 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(combined_audio)
        
        print(f"✓ Saved {len(combined_audio)} bytes to output_configured.wav")

asyncio.run(configured_streaming())
```

#### Example 3: Incremental Text Streaming (Low Latency)

```python
import asyncio
import websockets
import json

async def incremental_streaming():
    """
    Stream text sentence by sentence for lowest latency.
    Similar to ElevenLabs streaming API.
    """
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Configure for ultra-low latency
        await ws.send(json.dumps({
            "type": "config",
            "streaming": {
                "flush_threshold": 1,  # Flush after each sentence
                "optimize_streaming_latency": 4,  # Maximum speed
                "buffer_size": 1
            }
        }))
        
        await ws.recv()  # Wait for ready
        
        # Stream sentences one by one
        sentences = [
            "First sentence here.",
            "Second sentence follows.",
            "Third and final sentence."
        ]
        
        audio_file = open('incremental_output.pcm', 'wb')
        
        for i, sentence in enumerate(sentences, 1):
            print(f"\nSending sentence {i}: {sentence}")
            
            # Send text
            await ws.send(json.dumps({
                "type": "text",
                "text": sentence
            }))
            
            # Immediately start receiving audio
            first_chunk_received = False
            
            while True:
                message = await ws.recv()
                
                if isinstance(message, bytes):
                    if not first_chunk_received:
                        print(f"  → First audio chunk arrived!")
                        first_chunk_received = True
                    audio_file.write(message)
                else:
                    data = json.loads(message)
                    if data['type'] == 'audio_complete':
                        print(f"  → Sentence complete")
                        break
        
        audio_file.close()
        print("\n✓ All sentences synthesized")

asyncio.run(incremental_streaming())
```

#### Example 4: Control Messages

```python
import asyncio
import websockets
import json

async def control_messages_demo():
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Send some text
        await ws.send(json.dumps({
            "type": "text",
            "text": "This text is buffered."
        }))
        
        await asyncio.sleep(0.5)
        
        # Get statistics
        await ws.send(json.dumps({"type": "get_stats"}))
        stats = json.loads(await ws.recv())
        print(f"Stats: {stats}")
        
        # Reset buffer
        await ws.send(json.dumps({"type": "reset"}))
        reset_resp = json.loads(await ws.recv())
        print(f"Reset: {reset_resp['message']}")
        
        # Send more text
        await ws.send(json.dumps({
            "type": "text",
            "text": "New text after reset."
        }))
        
        # Force flush
        await ws.send(json.dumps({"type": "flush"}))
        
        # Receive all audio from flush
        while True:
            message = await ws.recv()
            if isinstance(message, str):
                data = json.loads(message)
                if data['type'] == 'flush_complete':
                    print("Flush complete!")
                    break

asyncio.run(control_messages_demo())
```

#### Example 5: Real-time Audio Playback

```python
import asyncio
import websockets
import json
import pyaudio

async def realtime_playback():
    """
    Play synthesized audio in real-time as it streams.
    Requires: pip install pyaudio
    """
    # Setup audio playback
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=24000,
        output=True,
        frames_per_buffer=1024
    )
    
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Configure for streaming
        await ws.send(json.dumps({
            "type": "config",
            "streaming": {
                "chunk_size": 1024,
                "optimize_streaming_latency": 3
            }
        }))
        
        await ws.recv()  # Ready
        
        # Send text
        text = "This audio will play in real-time as it is being synthesized!"
        await ws.send(json.dumps({
            "type": "text",
            "text": text
        }))
        
        # Play audio chunks as they arrive
        while True:
            message = await ws.recv()
            
            if isinstance(message, bytes):
                # Play audio immediately
                stream.write(message)
            else:
                data = json.loads(message)
                if data['type'] == 'audio_complete':
                    break
    
    # Cleanup
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    print("✓ Playback complete")

asyncio.run(realtime_playback())
```

---

## Configuration Guide

### Audio Configuration

```json
{
  "audio": {
    "sample_rate": 24000,     // Output sample rate (Hz)
    "channels": 1,            // 1=mono, 2=stereo
    "encoding": "pcm_s16le",  // Audio format
    "bitrate": 128            // For lossy formats (kbps)
  }
}
```

**Supported Encodings**:
- `pcm_s16le` - 16-bit PCM (default, best quality)
- `pcm_f32le` - 32-bit float PCM
- `wav` - WAV container format
- `mp3` - MP3 compressed (future)
- `opus` - Opus compressed (future)

### Voice Configuration

```json
{
  "voice": {
    "speaker": "default",     // Voice speaker ID
    "style": null,            // Speaking style (optional)
    "speed": 1.0,             // 0.5-2.0 (1.0 = normal)
    "pitch": 1.0,             // 0.5-2.0 (1.0 = normal)
    "energy": 1.0             // 0.5-2.0 (1.0 = normal)
  }
}
```

**Speed Examples**:
- `0.8` - 20% slower (clearer for learning)
- `1.0` - Normal speed
- `1.3` - 30% faster (energetic)

**Pitch Examples**:
- `0.8` - Lower pitch (deeper voice)
- `1.0` - Normal pitch
- `1.2` - Higher pitch (brighter voice)

### Streaming Configuration (ElevenLabs-style)

```json
{
  "streaming": {
    "enabled": true,
    "chunk_size": 1024,                      // Audio samples per chunk
    "flush_threshold": 3,                    // Sentences before auto-flush
    "optimize_streaming_latency": 2,         // 0-4 (0=quality, 4=speed)
    "enable_ssml_parsing": false,
    "buffer_size": 3,                        // Initial buffer chunks
    "sentence_silence_duration": 0.3         // Silence between sentences (s)
  }
}
```

**Flush Threshold**:
- `1` - Flush after each sentence (lowest latency)
- `2-3` - Balanced (recommended)
- `4-5` - More buffering (better quality)

**Latency Optimization Levels**:
- `0` - Best quality, higher latency
- `1` - High quality, moderate latency
- `2` - Balanced (default)
- `3` - Lower latency, good quality
- `4` - Lowest latency, acceptable quality

### Synthesis Configuration

```json
{
  "synthesis": {
    "stability": 0.5,              // 0.0-1.0 (consistency)
    "similarity_boost": 0.75,      // 0.0-1.0 (voice matching)
    "use_speaker_boost": true,
    "temperature": 0.7,            // 0.0-2.0 (randomness)
    "top_k": 50,                   // Top-K sampling
    "top_p": 0.9,                  // Nucleus sampling
    "repetition_penalty": 1.0,     // 1.0-2.0
    "max_new_tokens": 2048
  }
}
```

**Stability** (0.0 - 1.0):
- `0.0-0.3` - More expressive, variable
- `0.4-0.6` - Balanced (recommended)
- `0.7-1.0` - More consistent, stable

**Similarity Boost** (0.0 - 1.0):
- `0.5-0.7` - More creative interpretation
- `0.7-0.85` - Balanced (recommended)
- `0.85-1.0` - Closer to target voice

**Temperature** (0.0 - 2.0):
- `0.3-0.5` - More deterministic
- `0.6-0.8` - Balanced (default)
- `0.9-1.5` - More creative/varied

### Text Processing Configuration

```json
{
  "text_processing": {
    "normalize_text": true,         // Expand numbers, abbreviations
    "split_sentences": true,        // Auto-split into sentences
    "remove_special_chars": false,
    "max_sentence_length": 500      // Max chars per sentence
  }
}
```

---

## Code Examples

### Multi-Voice Conversation

```python
import requests
import base64
import wave

def synthesize_voice(text, speaker, output_file):
    response = requests.post('http://localhost:8002/synthesize', json={
        "text": text,
        "voice_config": {"speaker": speaker}
    })
    
    result = response.json()
    audio = base64.b64decode(result['audio_base64'])
    
    with wave.open(output_file, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(audio)

# Create conversation
synthesize_voice("Hello, how are you today?", "female_calm", "person1.wav")
synthesize_voice("I'm doing great, thanks!", "male_energetic", "person2.wav")
synthesize_voice("That's wonderful to hear!", "female_calm", "person3.wav")
```

### Batch Processing

```python
import requests
import base64
import wave
from concurrent.futures import ThreadPoolExecutor

texts = [
    "First paragraph of content.",
    "Second paragraph here.",
    "Third and final paragraph."
]

def synthesize_text(text, index):
    response = requests.post('http://localhost:8002/synthesize', json={
        "text": text
    })
    result = response.json()
    audio = base64.b64decode(result['audio_base64'])
    
    filename = f"output_{index:03d}.wav"
    with wave.open(filename, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(audio)
    
    return filename

# Process in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(synthesize_text, text, i) 
               for i, text in enumerate(texts)]
    
    for future in futures:
        filename = future.result()
        print(f"✓ Created {filename}")
```

### Adaptive Quality

```python
import requests
import time

def synthesize_adaptive(text, priority='balanced'):
    """
    Synthesize with quality settings based on priority.
    
    priority: 'speed', 'balanced', or 'quality'
    """
    configs = {
        'speed': {
            "synthesis": {"temperature": 1.0, "stability": 0.4},
            "streaming": {"optimize_streaming_latency": 4, "flush_threshold": 1}
        },
        'balanced': {
            "synthesis": {"temperature": 0.7, "stability": 0.5},
            "streaming": {"optimize_streaming_latency": 2, "flush_threshold": 2}
        },
        'quality': {
            "synthesis": {"temperature": 0.5, "stability": 0.7},
            "streaming": {"optimize_streaming_latency": 0, "flush_threshold": 3}
        }
    }
    
    config = configs.get(priority, configs['balanced'])
    
    start = time.time()
    response = requests.post('http://localhost:8002/synthesize', json={
        "text": text,
        **config
    })
    elapsed = time.time() - start
    
    result = response.json()
    print(f"Priority: {priority}")
    print(f"  Processing: {result['processing_time']:.3f}s")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  RTF: {result['realtime_factor']:.2f}x")
    
    return result

# Test different priorities
text = "This is a test of adaptive quality synthesis."
synthesize_adaptive(text, 'speed')
synthesize_adaptive(text, 'balanced')
synthesize_adaptive(text, 'quality')
```

---

## Best Practices

### 1. Text Optimization

✅ **DO**:
- Split long texts into paragraphs
- Use proper punctuation for natural pauses
- Keep sentences under 500 characters
- Normalize numbers and abbreviations

❌ **DON'T**:
- Send texts over 5000 characters
- Use excessive special characters
- Mix multiple languages without indication

### 2. Latency Optimization

For **real-time applications** (chatbots, voice assistants):
```json
{
  "streaming": {
    "flush_threshold": 1,
    "optimize_streaming_latency": 4,
    "buffer_size": 1
  }
}
```

For **quality-focused** (audiobooks, narration):
```json
{
  "synthesis": {
    "stability": 0.7,
    "temperature": 0.5
  },
  "streaming": {
    "optimize_streaming_latency": 0
  }
}
```

### 3. Error Handling

Always handle errors gracefully:

```python
import requests
from requests.exceptions import RequestException, Timeout

def safe_synthesize(text, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'http://localhost:8002/synthesize',
                json={"text": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Timeout:
            print(f"Attempt {attempt + 1}: Timeout")
            if attempt == max_retries - 1:
                raise
                
        except RequestException as e:
            print(f"Attempt {attempt + 1}: Error - {e}")
            if attempt == max_retries - 1:
                raise
    
    return None
```

### 4. Resource Management

Close WebSocket connections properly:

```python
import asyncio
import websockets

async def managed_connection():
    ws = None
    try:
        ws = await websockets.connect('ws://localhost:8002/stream')
        # ... use connection ...
    finally:
        if ws:
            await ws.close()
```

### 5. Audio Quality Verification

```python
import numpy as np

def verify_audio_quality(audio_bytes):
    """Basic audio quality checks"""
    audio = np.frombuffer(audio_bytes, dtype=np.int16)
    
    # Check for silence
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 100:
        print("⚠️ Warning: Audio may be too quiet")
    
    # Check for clipping
    clipping = np.sum(np.abs(audio) > 32000)
    if clipping > len(audio) * 0.01:
        print("⚠️ Warning: Audio may be clipping")
    
    # Check duration
    duration = len(audio) / 24000
    if duration < 0.1:
        print("⚠️ Warning: Audio is very short")
    
    return {
        "rms": rms,
        "clipping_samples": clipping,
        "duration": duration
    }
```

---

## Error Handling

### Common Error Codes

| Status Code | Error | Solution |
|-------------|-------|----------|
| 400 | Invalid request body | Check JSON format |
| 400 | Text too long | Split into smaller chunks (< 5000 chars) |
| 404 | Endpoint not found | Check URL |
| 500 | Synthesis failed | Check logs, retry |
| 503 | Service unavailable | Service not started or crashed |

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### WebSocket Errors

```json
{
  "type": "error",
  "message": "Error description"
}
```

### Error Handling Example

```python
import requests
from requests.exceptions import HTTPError

def handle_synthesis_errors(text):
    try:
        response = requests.post('http://localhost:8002/synthesize', json={
            "text": text
        })
        response.raise_for_status()
        return response.json()
        
    except HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()
            if "too long" in error['detail'].lower():
                print("Text is too long, splitting...")
                # Split and retry
                return synthesize_in_chunks(text)
            else:
                print(f"Bad request: {error['detail']}")
                
        elif e.response.status_code == 503:
            print("Service unavailable, retrying...")
            time.sleep(2)
            return handle_synthesis_errors(text)
            
        else:
            print(f"HTTP error: {e}")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

def synthesize_in_chunks(text, chunk_size=1000):
    """Split long text and synthesize in chunks"""
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    results = []
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        result = requests.post('http://localhost:8002/synthesize', json={
            "text": chunk
        }).json()
        results.append(result)
    
    return results
```

---

## Performance Tips

### 1. Connection Reuse

```python
import requests

# Create a session for connection pooling
session = requests.Session()

# Make multiple requests with same session
for text in texts:
    response = session.post('http://localhost:8002/synthesize', json={
        "text": text
    })
    # Process response...
```

### 2. Streaming for Large Texts

For texts > 1000 characters, use streaming:

```python
async def stream_long_text(text):
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Configure
        await ws.send(json.dumps({
            "type": "config",
            "streaming": {"flush_threshold": 2}
        }))
        await ws.recv()
        
        # Send text
        await ws.send(json.dumps({"type": "text", "text": text}))
        
        # Force flush to ensure processing
        await ws.send(json.dumps({"type": "flush"}))
        
        # Receive audio...
```

### 3. Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def synthesize_parallel(texts, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                requests.post,
                'http://localhost:8002/synthesize',
                json={"text": text}
            )
            for text in texts
        ]
        
        results = [f.result().json() for f in futures]
    
    return results

# Process 10 texts in parallel
texts = [f"Text number {i}" for i in range(10)]
results = synthesize_parallel(texts)
```

---

## Complete Integration Example

```python
"""
Complete TTS Client Example
Demonstrates all major features
"""

import asyncio
import requests
import websockets
import json
import wave
import base64
from pathlib import Path

class TTSClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/stream"
        self.session = requests.Session()
    
    def health_check(self):
        """Check if service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except:
            return None
    
    def list_voices(self):
        """Get available voices"""
        response = self.session.get(f"{self.base_url}/voices")
        return response.json()['voices']
    
    def synthesize(self, text, speaker="default", speed=1.0):
        """Simple synthesis"""
        response = self.session.post(f"{self.base_url}/synthesize", json={
            "text": text,
            "voice_config": {
                "speaker": speaker,
                "speed": speed
            }
        })
        return response.json()
    
    def save_synthesis(self, text, output_file, **kwargs):
        """Synthesize and save to file"""
        result = self.synthesize(text, **kwargs)
        audio_bytes = base64.b64decode(result['audio_base64'])
        
        with wave.open(output_file, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(result['sample_rate'])
            wav.writeframes(audio_bytes)
        
        return result
    
    async def stream_synthesis(self, text, config=None):
        """Stream synthesis via WebSocket"""
        async with websockets.connect(self.ws_url) as ws:
            # Send config if provided
            if config:
                await ws.send(json.dumps({"type": "config", **config}))
                await ws.recv()  # Wait for ready
            
            # Send text
            await ws.send(json.dumps({"type": "text", "text": text}))
            
            # Collect audio
            audio_chunks = []
            while True:
                message = await ws.recv()
                if isinstance(message, bytes):
                    audio_chunks.append(message)
                else:
                    data = json.loads(message)
                    if data['type'] == 'audio_complete':
                        break
            
            return b''.join(audio_chunks)

# Usage examples
async def main():
    client = TTSClient()
    
    # Check health
    health = client.health_check()
    if not health:
        print("Service not available!")
        return
    print(f"✓ Service healthy: {health['status']}")
    
    # List voices
    voices = client.list_voices()
    print(f"✓ Available voices: {len(voices)}")
    
    # Simple synthesis
    result = client.save_synthesis(
        "Hello, this is a test!",
        "output.wav",
        speaker="default",
        speed=1.0
    )
    print(f"✓ Synthesized: {result['audio_duration']:.2f}s")
    
    # Streaming synthesis
    audio = await client.stream_synthesis(
        "This is streaming synthesis!",
        config={
            "streaming": {
                "flush_threshold": 2,
                "optimize_streaming_latency": 3
            }
        }
    )
    
    # Save streamed audio
    with wave.open('streamed.wav', 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(audio)
    
    print(f"✓ Streamed: {len(audio)} bytes")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Additional Resources

- [README.md](README.md) - Service overview and setup
- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) - Complete configuration reference

---

**Questions or Issues?** Check the troubleshooting section in README.md or review the test_client.py for more examples.

