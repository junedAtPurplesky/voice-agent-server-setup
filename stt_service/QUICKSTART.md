# Faster Whisper STT Service v2.0 - Quick Start

High-performance speech-to-text with **client-side configuration** (like Speechmatics).

## Features

✓ **Client-configurable** audio format, VAD, and transcription settings  
✓ **Modular architecture** with clean separation of concerns  
✓ **GPU acceleration** with CUDA support  
✓ **Real-time streaming** with partial transcripts  
✓ **End-of-utterance detection** using VAD  
✓ **Multiple audio formats** (PCM16, PCM32, mu-law, A-law)  
✓ **Flexible VAD** (configurable per client)  

## Quick Setup

```bash
cd stt_service
./setup.sh
./stt_manager.sh start
```

## API Endpoints

### 1. Health Check
```bash
curl http://localhost:8001/health
```

### 2. Get Default Configuration
```bash
curl http://localhost:8001/config/defaults
```

### 3. Simple Transcription (POST)
```bash
curl -X POST http://localhost:8001/transcribe \
  -F "file=@audio.wav" \
  -F "language=en" \
  -F "beam_size=5"
```

### 4. Streaming WebSocket
Connect to `ws://localhost:8001/stream`

## Client-Side Configuration

### Connect with Custom Config

```python
import websockets
import json

async with websockets.connect("ws://localhost:8001/stream") as ws:
    # Send configuration
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
            "silence_duration": 1.0,
            "min_speech_duration": 0.3
        },
        "transcription": {
            "language": "en",
            "enable_partial_transcripts": True,
            "partial_interval": 0.5
        }
    }
    
    await ws.send(json.dumps(config))
    
    # Wait for ready
    response = await ws.recv()
    # {"type": "ready", "message": "Session configured"}
    
    # Send audio chunks
    await ws.send(audio_bytes)
```

## Configuration Options

### Audio Config
```json
{
  "sample_rate": 16000,        // 8000-48000 Hz
  "channels": 1,               // 1=mono, 2=stereo
  "encoding": "pcm_s16le"      // pcm_s16le, pcm_f32le, mulaw, alaw
}
```

### VAD Config
```json
{
  "enabled": true,
  "mode": 3,                   // 0-3 (0=quality, 3=aggressive)
  "silence_duration": 1.0,     // seconds of silence for end-of-utterance
  "min_speech_duration": 0.3,  // minimum speech duration to process
  "frame_duration": 30         // 10, 20, or 30 ms
}
```

### Transcription Config
```json
{
  "language": "en",                    // or null for auto-detect
  "task": "transcribe",                // or "translate"
  "beam_size": 5,
  "enable_partial_transcripts": true,
  "partial_interval": 0.5              // seconds between partials
}
```

## Message Types

### From Server
```json
{"type": "ready", "message": "...", "config": {...}}
{"type": "partial", "text": "...", "is_speaking": true}
{"type": "final", "text": "...", "segments": [...]}
{"type": "end_of_utterance"}
{"type": "status", "is_speaking": true}
{"type": "error", "message": "..."}
```

### From Client
```json
{"type": "config", "audio": {...}, "vad": {...}, "transcription": {...}}
{"type": "reset"}
{"type": "force_end"}
{"type": "get_stats"}
```

## Usage Examples

See `integration_example.py` for complete examples:
- Basic usage
- Custom configuration
- Voice agent integration
- Different audio formats
- VAD configurations

## Testing

```bash
source venv/bin/activate
python3 test_client.py
```

Tests include:
- Default configuration
- Custom configuration
- Control messages
- Different settings

## Service Management

```bash
./stt_manager.sh start    # Start service
./stt_manager.sh stop     # Stop service
./stt_manager.sh restart  # Restart
./stt_manager.sh status   # Check status
./stt_manager.sh logs     # View logs
```

## Architecture

```
stt_service/
├── config.py           # Configuration models (Pydantic)
├── audio_utils.py      # Audio format conversion
├── vad_processor.py    # Voice activity detection
├── transcription.py    # Whisper transcription engine
└── stt_server.py       # FastAPI server
```

## Performance Tips

1. **GPU**: Automatically uses CUDA if available
2. **Batch Size**: Adjust `beam_size` for speed/quality trade-off
3. **VAD Mode**: Higher mode = more aggressive = better in noise
4. **Sample Rate**: 16kHz is optimal for Whisper
5. **Partial Interval**: Lower = more responsive, higher = less CPU

## Replacing Speechmatics

This service provides a compatible API with similar features:
- Client-configurable audio format ✓
- Real-time streaming ✓
- Partial transcripts ✓
- End-of-utterance events ✓
- No external API costs ✓
- Full control over infrastructure ✓
