# Faster Whisper STT Service v2.0

Professional-grade Speech-to-Text service with **Speechmatics-like client-side configuration**.

## 🎯 Key Features

- ✅ **Fully Configurable** - Audio format, VAD, transcription settings from client
- ✅ **Modular Architecture** - Clean separation: config, audio utils, VAD, transcription, server
- ✅ **Multiple Audio Formats** - PCM16, PCM32, mu-law, A-law with auto-conversion
- ✅ **Smart VAD** - WebRTC-based voice activity detection with configurable sensitivity
- ✅ **Real-time Streaming** - Partial and final transcripts with end-of-utterance events
- ✅ **GPU Accelerated** - CUDA support for high performance
- ✅ **Isolated Environment** - Dedicated virtual environment, no dependency conflicts
- ✅ **Production Ready** - Service management scripts, logging, error handling

## 🚀 Quick Start

```bash
# Setup
./setup.sh

# Start service
./stt_manager.sh start

# Check status
./stt_manager.sh status

# Test
source venv/bin/activate
python3 test_client.py

# View logs
./stt_manager.sh logs
```

## 📁 Project Structure

```
stt_service/
├── config.py              # Pydantic configuration models
├── audio_utils.py         # Audio format conversion & processing
├── vad_processor.py       # Voice Activity Detection logic
├── transcription.py       # Whisper transcription engine
├── stt_server.py          # FastAPI server (main entry point)
├── requirements.txt       # Python dependencies
├── setup.sh              # Environment setup script
├── stt_manager.sh        # Service management (start/stop/status)
├── test_client.py        # Comprehensive test suite
├── integration_example.py # Integration examples
├── QUICKSTART.md         # Quick reference guide
├── CONFIG_REFERENCE.md   # Complete configuration documentation
└── README.md            # This file
```

## 🔌 API Overview

### HTTP Endpoints

```bash
# Health check
GET /health

# Get default configuration
GET /config/defaults

# Simple file transcription
POST /transcribe
```

### WebSocket Endpoint

```
ws://localhost:8001/stream
```

**Client sends:**
1. Configuration (JSON) - optional
2. Audio chunks (binary)
3. Control messages (JSON)

**Server sends:**
- `ready` - Configuration accepted
- `partial` - Partial transcript while speaking
- `final` - Final transcript with segments
- `end_of_utterance` - User stopped speaking
- `status` - Status updates
- `error` - Error messages

## 🎛️ Configuration Example

```python
import websockets
import json

async with websockets.connect("ws://localhost:8001/stream") as ws:
    # Configure the session
    config = {
        "type": "config",
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "encoding": "pcm_s16le"
        },
        "vad": {
            "enabled": True,
            "mode": 3,                    # 0-3, higher=more aggressive
            "silence_duration": 1.0,      # seconds before end-of-utterance
            "min_speech_duration": 0.3    # minimum speech to process
        },
        "transcription": {
            "language": "en",             # or None for auto-detect
            "beam_size": 5,               # higher=better quality
            "enable_partial_transcripts": True,
            "partial_interval": 0.5       # seconds between partials
        }
    }
    
    await ws.send(json.dumps(config))
    
    # Wait for ready
    response = json.loads(await ws.recv())
    # {"type": "ready", "message": "Session configured"}
    
    # Send audio
    await ws.send(audio_bytes)
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference for common tasks
- **[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)** - Complete configuration documentation
- **[integration_example.py](integration_example.py)** - Integration examples and patterns
- **[test_client.py](test_client.py)** - Test suite demonstrating all features

## 🔧 Service Management

```bash
./stt_manager.sh start    # Start service
./stt_manager.sh stop     # Stop service
./stt_manager.sh restart  # Restart service
./stt_manager.sh status   # Check status + health
./stt_manager.sh logs     # Tail logs in real-time
```

## 🎨 Usage Examples

### Basic Usage

```python
from integration_example import STTClient

stt = STTClient()

# Set callbacks
stt.on_partial = lambda text, meta: print(f"Partial: {text}")
stt.on_final = lambda text, meta: print(f"Final: {text}")
stt.on_end_of_utterance = lambda: print("User finished")

await stt.connect()
asyncio.create_task(stt.receive_messages())

# Send audio
await stt.send_audio(audio_chunk)
```

### Custom Configuration

```python
stt = STTClient(
    audio_config={"sample_rate": 48000, "channels": 2},
    vad_config={"mode": 2, "silence_duration": 0.8},
    transcription_config={"language": "en", "beam_size": 7}
)
```

### Different Audio Formats

```python
# Telephone audio (8kHz mu-law)
stt = STTClient(audio_config={
    "sample_rate": 8000,
    "encoding": "mulaw"
})

# High quality (48kHz stereo)
stt = STTClient(audio_config={
    "sample_rate": 48000,
    "channels": 2
})
```

## 🚦 Testing

Run the comprehensive test suite:

```bash
source venv/bin/activate
python3 test_client.py
```

Tests include:
- Health check
- Default configuration
- Simple file transcription
- Streaming with default config
- Streaming with custom config
- Control messages (reset, force_end, get_stats)

## 📊 Performance

- **Model**: Faster Whisper Large-v3 Turbo
- **Device**: CUDA (GPU) with CPU fallback
- **Latency**: ~100-300ms on GPU, ~1-3s on CPU
- **RTF**: 0.1-0.3x on GPU (10x-3x faster than real-time)
- **VRAM**: ~4-6GB on GPU

## 🔄 Replacing Speechmatics

This service provides equivalent functionality:

| Feature | Speechmatics | This Service |
|---------|--------------|--------------|
| Client-side config | ✅ | ✅ |
| Audio format config | ✅ | ✅ |
| Real-time streaming | ✅ | ✅ |
| Partial transcripts | ✅ | ✅ |
| End-of-utterance | ✅ | ✅ |
| Language detection | ✅ | ✅ |
| Local deployment | ❌ | ✅ |
| No API costs | ❌ | ✅ |
| Full control | ❌ | ✅ |

## 🛠️ Architecture

### Modular Design

The service follows clean architecture principles:

1. **config.py** - Configuration models (Pydantic validation)
2. **audio_utils.py** - Audio processing (format conversion, resampling)
3. **vad_processor.py** - VAD logic (WebRTC VAD, buffer management)
4. **transcription.py** - Transcription engine (Whisper model wrapper)
5. **stt_server.py** - Server logic (FastAPI, WebSocket handling)

### Session Flow

```
Client connects → Send config → Session created
                                     ↓
                              Audio converter
                                     ↓
                              VAD processor
                                     ↓
                          Transcription engine
                                     ↓
                         Results back to client
```

## 🔐 Security

- No authentication by default (add nginx/auth proxy for production)
- CORS enabled for all origins (configure for production)
- Runs on localhost by default
- Isolated virtual environment
- No data persistence

## 🐛 Troubleshooting

**Service won't start**
```bash
# Check logs
cat stt_service.log

# Check if port is in use
lsof -i :8001
```

**No GPU detected**
```bash
# Check CUDA
nvidia-smi

# Service will fall back to CPU automatically
```

**Poor transcription quality**
```bash
# Increase beam size in config
{"transcription": {"beam_size": 10}}

# Check audio format is correct
# Whisper expects 16kHz for best results
```

**VAD triggering incorrectly**
```bash
# Adjust VAD mode and thresholds
{"vad": {"mode": 2, "silence_duration": 1.5}}
```

## 📝 Requirements

- Python 3.9+
- CUDA 11.2+ (optional, for GPU)
- 8GB RAM minimum (4GB VRAM for GPU)
- Linux or macOS

## 🤝 Integration

The service is designed to integrate with:
- Voice agents
- Call centers
- Meeting transcription systems
- Live captioning systems
- Voice assistants

See `integration_example.py` for complete integration patterns.

## 📄 License

[Your license here]

## 🙋 Support

For issues or questions:
1. Check the documentation (QUICKSTART.md, CONFIG_REFERENCE.md)
2. Run test_client.py to verify setup
3. Check logs: `./stt_manager.sh logs`

---

**Built with**: Faster Whisper, FastAPI, WebRTC VAD, Pydantic

