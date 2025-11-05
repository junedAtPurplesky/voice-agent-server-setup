# CosyVoice TTS Service

Production-ready Text-to-Speech service using **official CosyVoice** implementation with real-time streaming capabilities and ElevenLabs-style configurations.

> **⚠️ IMPORTANT:** This service now follows the **official CosyVoice installation guide** from [github.com/FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice)

## 🌟 Features

### Core Capabilities
- ✅ **Official CosyVoice Implementation** - Following FunAudioLLM guidelines
- ✅ **High-Quality Speech Synthesis** - Multiple languages supported
- ✅ **Real-time Streaming** with WebSocket support
- ✅ **HTTP REST API** for simple integrations
- ✅ **Multiple Voice Support** - 7+ built-in speakers
- ✅ **Low Latency** streaming with optimized buffering

### ElevenLabs-Style Features
- 🎛️ **Flush Control** - Configure sentence buffering for optimal latency
- ⚡ **Latency Optimization** - 5-level streaming latency control (0-4)
- 🎚️ **Stability & Similarity** - Fine-tune voice consistency and characteristics
- 🎭 **Style Controls** - Speed, pitch, and energy adjustments
- 📊 **Real-time Stats** - Monitor processing and buffer status

### Production Ready
- 🔄 **Client-Configurable Parameters** - Full control over synthesis settings
- 🌐 **CORS Enabled** - Ready for web applications
- 📝 **Comprehensive Logging** - Track performance and debug issues
- 🛡️ **Error Handling** - Graceful fallbacks and error messages
- 🔧 **Management Scripts** - Easy start/stop/status commands

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Installation](#-installation)
3. [What Changed](#-what-changed-important)
4. [Usage](#-usage)
5. [API Endpoints](#-api-endpoints)
6. [Configuration](#-configuration)
7. [Examples](#-examples)
8. [Performance](#-performance)
9. [Troubleshooting](#-troubleshooting)

## 🚀 Quick Start

### Prerequisites

**⚠️ REQUIRED:** You must have **Conda (Miniconda or Anaconda)** installed!

```bash
# Install Miniconda (if not already installed)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### One-Line Setup

```bash
./setup.sh && ./start_service.sh
```

### Test the Service

```bash
# Activate environment first
source activate_env.sh

# Run comprehensive tests
python test_client.py

# Or test with curl
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test of the text-to-speech service!"}'
```

See **[INSTALLATION.md](INSTALLATION.md)** for detailed installation guide.

## 📦 Installation

### System Requirements

| Component | Required |
|-----------|----------|
| **Conda** | ✅ Required (Miniconda/Anaconda) |
| **Python** | 3.8 (specific version) |
| **RAM** | 8 GB minimum, 16 GB+ recommended |
| **Disk** | 5 GB+ (for models) |
| **GPU** | Optional (4GB+ VRAM for acceleration) |

### Prerequisites

1. **Conda (Required)**
   ```bash
   # Check if installed
   conda --version
   
   # If not installed:
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   bash Miniconda3-latest-Linux-x86_64.sh
   ```

2. **System Libraries**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y git git-lfs ffmpeg libsndfile1 sox
   
   # macOS
   brew install git git-lfs ffmpeg libsndfile sox
   
   # Initialize Git LFS
   git lfs install
   ```

### Automated Setup

```bash
cd tts_service

# Run official setup script
./setup.sh
```

The setup script will:
1. ✅ Verify Conda installation
2. ✅ Install system dependencies
3. ✅ Create conda environment `cosyvoice` with Python 3.8
4. ✅ Install PyTorch with CUDA support (if available)
5. ✅ Clone official CosyVoice repository with submodules
6. ✅ Install official dependencies from CosyVoice/requirements.txt
7. ✅ Configure Python import paths
8. ✅ Install service dependencies (FastAPI, etc.)
9. ✅ Test installation

**First Run**: Model (~1GB) downloads automatically on first use.

### Manual Installation

For manual installation or troubleshooting, see **[INSTALLATION.md](INSTALLATION.md)**.

## 🔄 What Changed? (IMPORTANT)

This service has been **completely refactored** to follow the official CosyVoice installation:

| Aspect | Old | New (Official) |
|--------|-----|----------------|
| Environment | Python venv | ✅ Conda |
| Python Version | 3.9+ | ✅ 3.8 (official requirement) |
| CosyVoice Source | Separate install | ✅ Official clone with submodules |
| Dependencies | Custom list | ✅ Official requirements.txt |
| Model | CosyVoice2-0.5B | ✅ CosyVoice-300M-SFT |
| API Calls | Custom | ✅ Official inference_sft API |
| Speakers | Hardcoded | ✅ Dynamic from model |

**See [SETUP_SUMMARY.md](SETUP_SUMMARY.md) for detailed migration guide.**

### If You Have Old Setup

```bash
# 1. Remove old virtual environment
rm -rf venv/

# 2. Install Conda (if not installed)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 3. Run new setup
./setup.sh
```

## 🎯 Usage

### Starting the Service

```bash
# Direct start
./start_service.sh

# Or use manager script
./tts_manager.sh start
```

The service will start on `http://localhost:8002`

### Service Management

```bash
# Check status
./tts_manager.sh status

# Stop service
./tts_manager.sh stop

# Restart service
./tts_manager.sh restart

# View logs
./tts_manager.sh logs
```

### Health Check

```bash
curl http://localhost:8002/health
```

## 🔌 API Endpoints

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/config/defaults` | GET | Get default configuration |
| `/voices` | GET | List available voices |
| `/synthesize` | POST | Synthesize text to speech |
| `/synthesize/stream` | POST | Streaming synthesis (HTTP) |

### WebSocket Endpoint

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/stream` | WebSocket | Real-time streaming TTS |

See [CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md) for detailed API documentation.

## ⚙️ Configuration

### Service Configuration (config.py)

```python
class ServiceConfig:
    model_name: str = "CosyVoice2-0.5B"
    host: str = "0.0.0.0"
    port: int = 8002
    device: str = "cuda" if available else "cpu"
    max_text_length: int = 5000
```

### Client Configuration

Clients can configure every aspect of synthesis:

```json
{
  "audio": {
    "sample_rate": 24000,
    "channels": 1,
    "encoding": "pcm_s16le"
  },
  "voice": {
    "speaker": "default",
    "speed": 1.0,
    "pitch": 1.0,
    "energy": 1.0
  },
  "streaming": {
    "enabled": true,
    "chunk_size": 1024,
    "flush_threshold": 3,
    "optimize_streaming_latency": 2
  },
  "synthesis": {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "temperature": 0.7
  }
}
```

See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) for complete configuration options.

## 📝 Examples

### HTTP Synthesis

```python
import requests
import base64
import wave

response = requests.post('http://localhost:8002/synthesize', json={
    "text": "Hello, this is a test!",
    "voice_config": {
        "speaker": "default",
        "speed": 1.0
    }
})

result = response.json()
audio_bytes = base64.b64decode(result['audio_base64'])

# Save to file
with wave.open('output.wav', 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(24000)
    wav.writeframes(audio_bytes)
```

### WebSocket Streaming

```python
import asyncio
import websockets
import json

async def stream_tts():
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Configure session
        await ws.send(json.dumps({
            "type": "config",
            "streaming": {
                "flush_threshold": 2,
                "optimize_streaming_latency": 3
            }
        }))
        
        # Wait for ready
        await ws.recv()
        
        # Send text
        await ws.send(json.dumps({
            "type": "text",
            "text": "Hello! This is streaming TTS."
        }))
        
        # Receive audio chunks
        while True:
            message = await ws.recv()
            if isinstance(message, bytes):
                # Process audio chunk
                print(f"Received {len(message)} bytes")
            else:
                data = json.loads(message)
                if data['type'] == 'audio_complete':
                    break

asyncio.run(stream_tts())
```

More examples in [CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md).

## 🚄 Performance

### Benchmark Results (Example)

| Metric | Value |
|--------|-------|
| Model Size | ~500MB |
| GPU Memory | ~2GB (synthesis) |
| CPU Synthesis RTF | ~0.5x (varies by CPU) |
| GPU Synthesis RTF | ~15x (RTX 3090) |
| Streaming Latency | 100-300ms (optimized) |
| Max Text Length | 5000 chars |

**RTF (Real-Time Factor)**: Lower is better. 1.0x = real-time, 0.5x = 2x slower, 2.0x = 2x faster.

### Optimization Tips

1. **GPU Acceleration**: Use CUDA for 10-30x faster synthesis
2. **Flush Threshold**: Lower values (1-2) for lower latency
3. **Latency Optimization**: Set to 3-4 for fastest streaming
4. **Chunk Size**: 512-1024 samples for optimal streaming

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
./tts_manager.sh logs

# Common issues:
# 1. Virtual environment not created
./setup.sh

# 2. CosyVoice not installed
cd CosyVoice && git pull && pip install -r requirements.txt

# 3. Model download failed
rm -rf models/  # Will re-download on next start
```

### CUDA Out of Memory

```python
# Reduce model precision or use CPU
export CUDA_VISIBLE_DEVICES=""  # Force CPU
./start_service.sh
```

### Audio Quality Issues

```json
{
  "synthesis": {
    "stability": 0.7,  // Increase for more consistent output
    "temperature": 0.5  // Decrease for more deterministic results
  }
}
```

### Streaming Latency Too High

```json
{
  "streaming": {
    "flush_threshold": 1,  // Flush after each sentence
    "optimize_streaming_latency": 4,  // Maximum speed
    "buffer_size": 1  // Minimum buffering
  }
}
```

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md) - Complete API reference with examples
- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) - Detailed configuration options

## 🏗️ Architecture

```
tts_service/
├── config.py              # Configuration models (Pydantic)
├── tts_server.py          # FastAPI server (HTTP + WebSocket)
├── synthesis.py           # CosyVoice2 synthesis engine
├── audio_utils.py         # Audio processing utilities
├── text_processor.py      # Text processing and buffering
├── test_client.py         # Comprehensive test suite
├── requirements.txt       # Python dependencies
├── setup.sh              # Setup script
├── start_service.sh      # Start script
├── stop_service.sh       # Stop script
└── tts_manager.sh        # Service manager
```

## 🔗 Related Services

This TTS service is designed to work seamlessly with:
- **STT Service** (port 8001) - Speech-to-Text
- **LLM Gateway** (port 3000) - Language model inference

Together they form a complete voice AI pipeline.

## 📄 License

This service uses CosyVoice2 which is released under Apache 2.0 License.

## 🤝 Contributing

Issues and pull requests are welcome! Please ensure:
1. Code follows existing patterns
2. All tests pass
3. Documentation is updated

## 🙏 Acknowledgments

- **FunAudioLLM Team** for CosyVoice2 model
- **FastAPI** for the excellent web framework
- **PyTorch** for deep learning capabilities

---

**Need Help?** Check the troubleshooting section or review the comprehensive guides in the documentation folder.

