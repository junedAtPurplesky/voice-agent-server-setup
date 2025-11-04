# STT Service - Client API Guide

## 🎯 Overview

This Speech-to-Text (STT) service provides real-time and batch audio transcription using OpenAI's Whisper model. The service is designed with **client-side configuration**, allowing you to customize audio format, Voice Activity Detection (VAD), and transcription settings per session.

### Key Features

- ✅ **Real-time streaming** with WebSocket support
- ✅ **Batch transcription** via HTTP POST
- ✅ **Client-configurable** audio format, VAD, and transcription settings
- ✅ **Partial transcripts** for real-time feedback
- ✅ **Voice Activity Detection (VAD)** for automatic utterance segmentation
- ✅ **Multi-language support** (100+ languages via Whisper)
- ✅ **Multiple audio formats** (PCM16, PCM32, mu-law, A-law)
- ✅ **GPU-accelerated** for low latency

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8001
```

### Available Endpoints

| Endpoint | Method | Type | Description |
|----------|--------|------|-------------|
| `/health` | GET | HTTP | Health check |
| `/config/defaults` | GET | HTTP | Get default configuration |
| `/transcribe` | POST | HTTP | Batch file transcription |
| `/stream` | WebSocket | WS | Real-time streaming transcription |

---

## 📡 HTTP Endpoints

### 1. Health Check

Check if the service is running and get system information.

**Request:**
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "model_name": "large-v3",
  "device": "cuda",
  "compute_type": "float16"
}
```

**Example:**
```bash
curl http://localhost:8001/health
```

---

### 2. Get Default Configuration

Retrieve the default configuration settings.

**Request:**
```bash
GET /config/defaults
```

**Response:**
```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "encoding": "pcm_s16le",
    "chunk_size": null
  },
  "vad": {
    "enabled": true,
    "mode": 3,
    "silence_duration": 1.0,
    "min_speech_duration": 0.3,
    "frame_duration": 30,
    "speech_threshold": 0.5
  },
  "transcription": {
    "language": null,
    "task": "transcribe",
    "beam_size": 5,
    "best_of": 5,
    "temperature": 0.0,
    "vad_filter": false,
    "condition_on_previous_text": false,
    "no_speech_threshold": 0.6,
    "enable_partial_transcripts": true,
    "partial_interval": 0.5
  }
}
```

**Example:**
```bash
curl http://localhost:8001/config/defaults
```

---

### 3. Batch File Transcription

Upload an audio file for transcription.

**Request:**
```bash
POST /transcribe
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Audio file (WAV, MP3, etc.) |
| `language` | String | No | Language code (e.g., "en", "es", "hi") |
| `task` | String | No | "transcribe" or "translate" |
| `beam_size` | Integer | No | Beam size (1-10, default: 5) |
| `temperature` | Float | No | Sampling temperature (0.0-1.0) |

**Response:**
```json
{
  "text": "This is the transcribed text.",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "This is the transcribed text."
    }
  ],
  "language": "en",
  "language_probability": 0.98,
  "processing_time": 0.523,
  "audio_duration": 2.5,
  "realtime_factor": 0.21
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8001/transcribe \
  -F "file=@audio.wav" \
  -F "language=en" \
  -F "beam_size=5"
```

**Example (Python):**
```python
import requests

url = "http://localhost:8001/transcribe"
files = {"file": open("audio.wav", "rb")}
data = {
    "language": "en",
    "beam_size": 5
}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result["text"])
```

---

## 🔄 WebSocket Endpoint (Real-Time Streaming)

The WebSocket endpoint provides real-time transcription with partial results and Voice Activity Detection.

### Connection

```
ws://localhost:8001/stream
```

### Message Flow

```
Client                           Server
  |                                |
  |-- 1. Connect WebSocket ------->|
  |                                |
  |-- 2. Send Configuration ------>|
  |<---- Ready Confirmation -------|
  |                                |
  |-- 3. Stream Audio Chunks ----->|
  |<---- Partial Transcripts ------|
  |<---- Final Transcripts --------|
  |<---- End-of-Utterance ---------|
  |                                |
  |-- 4. Control Messages -------->|
  |<---- Status/Stats -------------|
  |                                |
  |-- 5. Close Connection -------->|
```

---

## 📤 Client → Server Messages

### 1. Configuration Message (First Message)

Send configuration as the **first message** after connecting.

```json
{
  "type": "config",
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "vad": {
    "enabled": true,
    "mode": 3,
    "silence_duration": 1.0,
    "min_speech_duration": 0.3,
    "frame_duration": 30,
    "speech_threshold": 0.5
  },
  "transcription": {
    "language": "en",
    "task": "transcribe",
    "beam_size": 5,
    "enable_partial_transcripts": true,
    "partial_interval": 0.5
  }
}
```

**Note:** Configuration is optional. If not sent, defaults will be used.

---

### 2. Audio Data (Binary)

Send raw audio bytes as binary WebSocket messages.

**Requirements:**
- Audio must match the configured format
- Default: 16kHz, mono, PCM 16-bit signed little-endian
- Recommended chunk size: 100-200ms (3200-6400 bytes for 16kHz mono PCM16)

---

### 3. Control Messages (JSON)

#### Reset Buffer
```json
{
  "type": "reset"
}
```
Clears the audio buffer and resets VAD state.

#### Force End of Utterance
```json
{
  "type": "force_end"
}
```
Forces transcription of current buffer and triggers end-of-utterance.

#### Get Statistics
```json
{
  "type": "get_stats"
}
```
Request current session statistics.

---

## 📥 Server → Client Messages

All messages from server are JSON format.

### 1. Ready Confirmation

Sent after configuration is accepted.

```json
{
  "type": "ready",
  "message": "Session configured and ready"
}
```

---

### 2. Partial Transcript

Sent periodically during speech (based on `partial_interval`).

```json
{
  "type": "partial",
  "text": "This is a partial transcri",
  "timestamp": 1699123456.789
}
```

---

### 3. Final Transcript

Sent when utterance is complete (triggered by VAD silence detection).

```json
{
  "type": "final",
  "text": "This is the complete final transcript.",
  "segments": [
    {
      "start": 0.0,
      "end": 3.2,
      "text": "This is the complete final transcript."
    }
  ],
  "language": "en",
  "language_probability": 0.98,
  "processing_time": 0.156,
  "audio_duration": 3.2,
  "realtime_factor": 0.05
}
```

---

### 4. End of Utterance

Sent when VAD detects silence (user stopped speaking).

```json
{
  "type": "end_of_utterance",
  "message": "End of utterance detected"
}
```

---

### 5. Status Message

Sent for various status updates.

```json
{
  "type": "status",
  "message": "Buffer reset",
  "is_speaking": false,
  "speech_duration": 0.0,
  "silence_duration": 0.0
}
```

---

### 6. Statistics

Response to `get_stats` request.

```json
{
  "type": "stats",
  "is_speaking": true,
  "speech_duration": 5.2,
  "silence_duration": 0.0,
  "buffer_size": 83200,
  "frame_buffer_size": 960,
  "total_speech_frames": 173
}
```

---

### 7. Error Message

Sent when an error occurs.

```json
{
  "type": "error",
  "error": "Invalid audio format",
  "details": "Expected 16000 Hz, got 8000 Hz"
}
```

---

## ⚙️ Configuration Options

### Audio Configuration

```json
{
  "audio": {
    "sample_rate": 16000,     // Hz: 8000, 16000, 44100, 48000, etc.
    "channels": 1,            // 1 = mono, 2 = stereo
    "encoding": "pcm_s16le",  // "pcm_s16le", "pcm_f32le", "mulaw", "alaw"
    "chunk_size": null        // Optional: expected chunk size in bytes
  }
}
```

**Supported Encodings:**
- `pcm_s16le` - 16-bit signed PCM, little-endian (default, recommended)
- `pcm_f32le` - 32-bit float PCM, little-endian
- `mulaw` - 8-bit mu-law (telephone quality)
- `alaw` - 8-bit A-law (telephone quality)

---

### VAD (Voice Activity Detection) Configuration

```json
{
  "vad": {
    "enabled": true,              // Enable/disable VAD
    "mode": 3,                    // 0-3 (0=quality, 3=aggressive)
    "silence_duration": 1.0,      // Seconds of silence to trigger end (0.1-5.0)
    "min_speech_duration": 0.3,   // Minimum speech duration to process (0.1-2.0)
    "frame_duration": 30,         // Frame size in ms (10, 20, or 30)
    "speech_threshold": 0.5       // Speech detection threshold (0.0-1.0)
  }
}
```

**VAD Mode:**
- `0` - Quality mode (less aggressive, may miss short pauses)
- `1` - Low bitrate mode
- `2` - Aggressive mode
- `3` - Very aggressive mode (recommended for real-time)

**Silence Duration:**
- Lower values = more frequent end-of-utterance events
- Higher values = longer utterances before segmentation
- Recommended: 0.7-1.5 seconds

---

### Transcription Configuration

```json
{
  "transcription": {
    "language": "en",                       // Language code or null for auto-detect
    "task": "transcribe",                   // "transcribe" or "translate"
    "beam_size": 5,                         // Beam search size (1-10)
    "best_of": 5,                           // Number of candidates (1-10)
    "temperature": 0.0,                     // Sampling temperature (0.0-1.0)
    "vad_filter": false,                    // Use Whisper's internal VAD
    "condition_on_previous_text": false,    // Use previous context
    "no_speech_threshold": 0.6,             // No-speech detection (0.0-1.0)
    "enable_partial_transcripts": true,     // Enable partial results
    "partial_interval": 0.5                 // Partial frequency in seconds (0.1-2.0)
  }
}
```

**Language Codes:** (Examples)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `hi` - Hindi
- `zh` - Chinese
- `ja` - Japanese
- `null` - Auto-detect

**Task:**
- `transcribe` - Transcribe audio in original language
- `translate` - Translate to English

**Beam Size:**
- Lower = faster, less accurate
- Higher = slower, more accurate
- Recommended: 5-7

**Partial Interval:**
- How often partial transcripts are sent while speaking
- Lower = more frequent updates, higher overhead
- Higher = less frequent updates
- Recommended: 0.3-0.5 seconds

---

## 💻 Code Examples

### Python - Real-Time Streaming

```python
import asyncio
import websockets
import json
import pyaudio

async def stream_audio():
    # Connect to WebSocket
    async with websockets.connect("ws://localhost:8001/stream") as websocket:
        
        # 1. Send configuration
        config = {
            "type": "config",
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "encoding": "pcm_s16le"
            },
            "vad": {
                "enabled": True,
                "mode": 3,
                "silence_duration": 1.0
            },
            "transcription": {
                "language": "en",
                "enable_partial_transcripts": True,
                "partial_interval": 0.5
            }
        }
        
        await websocket.send(json.dumps(config))
        
        # 2. Wait for ready
        response = json.loads(await websocket.recv())
        print(f"Status: {response['message']}")
        
        # 3. Set up audio capture
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=3200
        )
        
        # 4. Handle incoming messages
        async def receive_messages():
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'partial':
                    print(f"Partial: {data['text']}")
                    
                elif data['type'] == 'final':
                    print(f"Final: {data['text']}")
                    
                elif data['type'] == 'end_of_utterance':
                    print("--- End of utterance ---")
        
        # 5. Send audio in parallel
        async def send_audio():
            try:
                while True:
                    audio_data = stream.read(3200, exception_on_overflow=False)
                    await websocket.send(audio_data)
                    await asyncio.sleep(0.1)  # 100ms chunks
            except KeyboardInterrupt:
                pass
        
        # Run both tasks
        await asyncio.gather(
            receive_messages(),
            send_audio()
        )

# Run the client
asyncio.run(stream_audio())
```

---

### JavaScript - Real-Time Streaming

```javascript
const ws = new WebSocket('ws://localhost:8001/stream');

ws.onopen = () => {
    // Send configuration
    const config = {
        type: 'config',
        audio: {
            sample_rate: 16000,
            channels: 1,
            encoding: 'pcm_s16le'
        },
        vad: {
            enabled: true,
            mode: 3,
            silence_duration: 1.0
        },
        transcription: {
            language: 'en',
            enable_partial_transcripts: true,
            partial_interval: 0.5
        }
    };
    
    ws.send(JSON.stringify(config));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'ready':
            console.log('Connected:', data.message);
            startAudioCapture();
            break;
            
        case 'partial':
            console.log('Partial:', data.text);
            updateUI(data.text, false);
            break;
            
        case 'final':
            console.log('Final:', data.text);
            updateUI(data.text, true);
            break;
            
        case 'end_of_utterance':
            console.log('--- End of utterance ---');
            break;
            
        case 'error':
            console.error('Error:', data.error);
            break;
    }
};

function startAudioCapture() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const audioContext = new AudioContext({ sampleRate: 16000 });
            const source = audioContext.createMediaStreamSource(stream);
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            
            processor.onaudioprocess = (e) => {
                const audioData = e.inputBuffer.getChannelData(0);
                
                // Convert float32 to int16
                const int16 = new Int16Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    int16[i] = Math.max(-32768, Math.min(32767, audioData[i] * 32768));
                }
                
                // Send to WebSocket
                ws.send(int16.buffer);
            };
            
            source.connect(processor);
            processor.connect(audioContext.destination);
        });
}
```

---

### Python - Batch Transcription

```python
import requests

def transcribe_file(audio_path, language='en'):
    url = "http://localhost:8001/transcribe"
    
    with open(audio_path, 'rb') as audio_file:
        files = {'file': audio_file}
        data = {
            'language': language,
            'beam_size': 5
        }
        
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"Transcription: {result['text']}")
        print(f"Language: {result['language']} ({result['language_probability']:.2%})")
        print(f"Duration: {result['audio_duration']:.2f}s")
        print(f"Processing time: {result['processing_time']:.3f}s")
        print(f"Real-time factor: {result['realtime_factor']:.2f}x")
        
        return result

# Usage
result = transcribe_file('audio.wav', language='en')
```

---

## 🎯 Common Use Cases

### 1. Real-Time Voice Assistant

```python
config = {
    "vad": {
        "mode": 3,                    # Aggressive VAD
        "silence_duration": 0.8,      # Quick response
        "min_speech_duration": 0.2
    },
    "transcription": {
        "language": "en",
        "enable_partial_transcripts": True,
        "partial_interval": 0.3       # Frequent updates
    }
}
```

---

### 2. Meeting Transcription

```python
config = {
    "vad": {
        "mode": 2,                    # Balanced
        "silence_duration": 1.5,      # Longer utterances
        "min_speech_duration": 0.5
    },
    "transcription": {
        "language": None,             # Auto-detect
        "enable_partial_transcripts": False,  # Only finals
        "beam_size": 7                # Higher quality
    }
}
```

---

### 3. Telephone Call Transcription

```python
config = {
    "audio": {
        "sample_rate": 8000,          # Telephone quality
        "encoding": "mulaw"
    },
    "vad": {
        "mode": 3,
        "silence_duration": 1.0
    },
    "transcription": {
        "language": "en",
        "beam_size": 5
    }
}
```

---

### 4. High-Quality Archival

```python
config = {
    "vad": {
        "enabled": False              # Disable VAD for continuous
    },
    "transcription": {
        "language": "en",
        "beam_size": 10,              # Maximum quality
        "temperature": 0.0,
        "enable_partial_transcripts": False
    }
}
```

---

## 📊 Performance Characteristics

### Latency

| Model | RTF (Real-Time Factor) | Latency (1s audio) |
|-------|------------------------|-------------------|
| tiny | 0.05x | ~50ms |
| base | 0.1x | ~100ms |
| small | 0.15x | ~150ms |
| medium | 0.2x | ~200ms |
| large-v3 | 0.3x | ~300ms |

**RTF Explanation:**
- 0.1x = Processing is 10x faster than real-time
- 1.0x = Processing equals real-time
- Lower is better

---

### Throughput

The service can handle:
- **Real-time**: Multiple concurrent streams (depends on GPU)
- **Batch**: Limited by GPU memory and model size

**Recommended Limits:**
- Small model: 10-20 concurrent streams
- Large-v3 model: 5-10 concurrent streams (depends on GPU)

---

## 🔧 Troubleshooting

### Connection Issues

**Problem:** WebSocket connection refused
```
Solution: Ensure service is running on port 8001
Check: curl http://localhost:8001/health
```

---

### Audio Format Errors

**Problem:** `Invalid audio format` error
```
Solution: Verify your audio matches the configured format
- Sample rate must match
- Channels must match
- Encoding must match
- Audio must be raw PCM (no headers) for streaming
```

---

### No Transcription Output

**Problem:** Empty transcription results
```
Possible causes:
1. Audio volume too low
2. Wrong audio format
3. VAD filtering out audio as non-speech
4. Language mismatch

Solutions:
- Check audio levels
- Verify format configuration
- Disable VAD temporarily: "vad": {"enabled": false}
- Try language auto-detect: "language": null
```

---

### VAD Not Triggering

**Problem:** No end-of-utterance events
```
Solutions:
- Increase VAD mode: "mode": 3
- Decrease silence_duration: "silence_duration": 0.7
- Check if audio contains actual pauses
```

---

### Slow Processing

**Problem:** High latency or RTF > 1.0
```
Possible causes:
1. CPU mode (instead of GPU)
2. Large model on limited hardware
3. High beam_size setting

Solutions:
- Verify GPU is being used (check /health endpoint)
- Use smaller model
- Reduce beam_size to 3-5
```

---

## 📝 Best Practices

### 1. Audio Configuration
- Use 16kHz sample rate for best quality/performance balance
- Use mono audio when possible (lower bandwidth)
- Use PCM16 encoding for lowest latency

### 2. VAD Settings
- Start with default settings
- Adjust `silence_duration` based on your use case:
  - Interactive: 0.7-1.0s
  - Dictation: 1.0-1.5s
  - Meetings: 1.5-2.0s

### 3. Partial Transcripts
- Enable for real-time user feedback
- Set `partial_interval` to 0.3-0.5s
- Remember partials may change (not final until `final` event)

### 4. Language Detection
- Specify language if known (faster and more accurate)
- Use `null` for auto-detect only when necessary
- Common codes: `en`, `es`, `fr`, `de`, `hi`, `zh`, `ja`

### 5. Error Handling
- Always handle `error` message type
- Implement reconnection logic for WebSocket
- Validate audio format before sending

---

## 🆘 Support

For issues or questions:

1. Check service logs: `./stt_manager.sh logs`
2. Verify service health: `curl http://localhost:8001/health`
3. Test with provided test client: `python3 test_client.py`
4. Review configuration documentation: `CONFIG_REFERENCE.md`

---

## 📄 License

[Your License Here]

---

**Built with:** Faster Whisper, FastAPI, WebRTC VAD, Pydantic
**Version:** 2.0.0

