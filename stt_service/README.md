# STT Service - Production Ready Speech-to-Text

## 🚀 Overview

A production-ready Speech-to-Text service built with FastAPI, featuring:
- **Dynamic Configuration**: Language selection, VAD parameters configurable at runtime
- **Multiple Service Types**: HTTP file upload, HTTP streaming, Real-time WebSocket, Full-duplex WebSocket with VAD
- **Voice Activity Detection**: Configurable VAD with speech start/end events
- **Production Security**: API key authentication, request validation, rate limiting
- **Shell-based Deployment**: No Docker required - perfect for RunPod and similar platforms

## 📋 Features

### Core Capabilities
- ✅ **30+ Languages Supported** with auto-detection
- ✅ **Configurable VAD** with threshold and duration parameters
- ✅ **Real-time Streaming** via WebSocket
- ✅ **Full-duplex Communication** with VAD events
- ✅ **Production Security** with authentication and validation
- ✅ **Comprehensive Monitoring** with health checks and metrics

### Service Endpoints
1. **HTTP File Transcription** - Upload audio files for transcription
2. **HTTP Stream Transcription** - Send raw audio data for transcription
3. **WebSocket Real-time** - Live streaming transcription with partial results
4. **WebSocket Full-duplex** - Advanced streaming with VAD events (speech_start, speech_end)

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- 8GB+ RAM (16GB+ recommended for large models)
- ffmpeg and libsndfile1

### Installation on RunPod

```bash
# 1. Clone or upload the code
cd /workspace
git clone <your-repo-url> stt_service
cd stt_service

# 2. Validate deployment
./validate_deployment.sh

# 3. Run setup (installs dependencies)
./setup.sh

# 4. Configure service
cp .env.example .env
nano .env  # Edit as needed

# 5. Start service
./start.sh

# 6. Check status
./status.sh
```

### Installation on Other Systems

```bash
# 1. Navigate to service directory
cd stt_service

# 2. Validate deployment
chmod +x *.sh
./validate_deployment.sh

# 3. Setup
./setup.sh

# 4. Configure
cp .env.example .env
# Edit .env with your settings

# 5. Start
./start.sh
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Model Configuration
STT_MODEL_NAME=large-v3-turbo  # Model size
STT_DEVICE=cuda                # cuda or cpu
STT_COMPUTE_TYPE=int8          # int8, float16, float32

# Authentication
STT_API_KEY=your_secure_key_here

# VAD Configuration
STT_VAD_ENABLED=true
STT_VAD_THRESHOLD=0.5          # 0.0 to 1.0
STT_VAD_MIN_SPEECH_DURATION_MS=250
STT_VAD_MIN_SILENCE_DURATION_MS=200

# Service Configuration
STT_HOST=0.0.0.0
STT_PORT=8000
STT_MAX_FILE_SIZE_MB=100
STT_MAX_WEBSOCKET_CONNECTIONS=100
```

### Model Options

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1GB | Fastest | Lowest |
| base | ~1GB | Very Fast | Low |
| small | ~2GB | Fast | Good |
| medium | ~5GB | Medium | Better |
| large-v3-turbo | ~6GB | Slower | Best |

## 📡 API Usage

### HTTP File Transcription

```bash
curl -X POST "http://localhost:8000/stt/transcribe" \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@audio.wav" \
  -F "language=hi"
```

Response:
```json
{
  "success": true,
  "text": "transcribed text here",
  "language": "hi",
  "duration": 2.5,
  "segments": [...],
  "processing_time": 1.2
}
```

### WebSocket Real-time

```javascript
const ws = new WebSocket('ws://localhost:8000/stt/ws/realtime?token=your_api_key&language=hi');

ws.onopen = () => {
    // Send audio chunks
    ws.send(audioChunk);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'partial_transcript') {
        console.log('Partial:', data.text);
    }
};
```

### WebSocket Full-duplex with VAD

```javascript
const ws = new WebSocket('ws://localhost:8000/stt/ws/fullduplex?token=your_api_key&language=hi');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'vad_event':
            if (data.event === 'speech_start') {
                console.log('User started speaking');
            } else if (data.event === 'speech_end') {
                console.log('User stopped speaking');
            }
            break;
        case 'partial_transcript':
            console.log('Partial:', data.text);
            break;
        case 'final_transcript':
            console.log('Final:', data.text);
            break;
    }
};
```

## 🎯 Service Management

### Start Service
```bash
./start.sh
```

### Stop Service
```bash
./stop.sh
```

### Restart Service
```bash
./restart.sh
```

### Check Status
```bash
./status.sh
```

### View Logs
```bash
# Real-time
tail -f logs/stt_service.log

# Last 100 lines
tail -n 100 logs/stt_service.log

# Search for errors
grep ERROR logs/stt_service.log
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/stt/health
```

### Service Status
```bash
./status.sh
```

### Logs
- Main log: `logs/stt_service.log`
- PID file: `stt_service.pid`

## 🔒 Security

### Change Default API Key
```bash
# Generate secure key
openssl rand -hex 32

# Update .env
STT_API_KEY=your_new_secure_key
```

### Authentication
All endpoints except `/health` and `/` require authentication:
```bash
Authorization: Bearer your_api_key
```

## 🐛 Troubleshooting

### Service Won't Start

1. Check logs:
```bash
cat logs/stt_service.log
```

2. Check if port is in use:
```bash
netstat -tuln | grep 8000
```

3. Kill existing process:
```bash
./stop.sh
./start.sh
```

### CUDA Not Available

Switch to CPU mode:
```bash
# Edit .env
STT_DEVICE=cpu
STT_COMPUTE_TYPE=float32
```

### Out of Memory

Use smaller model:
```bash
# Edit .env
STT_MODEL_NAME=base  # or tiny, small
```

### Model Download Issues

```bash
# Pre-download model
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu')"
```

## 📚 Documentation

- [RunPod Deployment Guide](RUNPOD_DEPLOYMENT.md) - Detailed deployment instructions for RunPod
- [API Documentation](http://localhost:8000/stt/docs) - Interactive API docs (when service is running)

## 🧪 Testing

### Run Test Suite
```bash
python3 test_service.py
```

### Manual Tests
```bash
# Health check
curl http://localhost:8000/stt/health

# Service info
curl http://localhost:8000/stt/

# Configuration
curl -H "Authorization: Bearer your_api_key" http://localhost:8000/stt/config
```

## 🌐 Exposing Service Externally

### Option 1: RunPod Public Port
- In RunPod dashboard, expose port 8000
- Access via: `https://your-pod-id-8000.proxy.runpod.net/stt/`

### Option 2: ngrok (for testing)
```bash
ngrok http 8000
```

### Option 3: Custom Domain
Set up reverse proxy with nginx or caddy.

## 📈 Performance Optimization

### For High-end GPUs (A100, A6000)
```bash
STT_COMPUTE_TYPE=float16
STT_MODEL_NAME=large-v3-turbo
```

### For Mid-range GPUs (RTX 3090, 4090)
```bash
STT_COMPUTE_TYPE=int8
STT_MODEL_NAME=large-v3-turbo
```

### For Low-end GPUs or CPU
```bash
STT_DEVICE=cpu
STT_COMPUTE_TYPE=int8
STT_MODEL_NAME=base
```

## 🔄 Updating

```bash
# Pull latest code
git pull

# Stop service
./stop.sh

# Update dependencies
pip3 install -r requirements.txt --upgrade

# Start service
./start.sh
```

## 📦 File Structure

```
stt_service/
├── app/                      # Application code
│   ├── __init__.py
│   ├── main.py              # Main application
│   ├── config.py            # Configuration management
│   ├── models.py            # STT models and processors
│   ├── vad.py               # Voice Activity Detection
│   ├── auth.py              # Authentication
│   ├── utils.py             # Utilities
│   ├── http_endpoints.py    # HTTP endpoints
│   └── websocket_endpoints.py # WebSocket endpoints
├── logs/                     # Service logs
├── tmp/                      # Temporary files
├── setup.sh                  # Setup script
├── start.sh                  # Start service
├── stop.sh                   # Stop service
├── restart.sh                # Restart service
├── status.sh                 # Check status
├── validate_deployment.sh    # Validate setup
├── test_service.py           # Test script
├── requirements.txt          # Python dependencies
├── .env.example              # Example configuration
└── README.md                 # This file
```

## 🤝 Support

For issues:
1. Check logs: `tail -f logs/stt_service.log`
2. Validate setup: `./validate_deployment.sh`
3. Run tests: `python3 test_service.py`
4. Review [RUNPOD_DEPLOYMENT.md](RUNPOD_DEPLOYMENT.md)

## 📝 License

This project is licensed under the MIT License.

## 🎉 Quick Command Reference

```bash
# Setup
./setup.sh                    # Initial setup
./validate_deployment.sh      # Validate deployment

# Service Management
./start.sh                    # Start service
./stop.sh                     # Stop service
./restart.sh                  # Restart service
./status.sh                   # Check status

# Monitoring
tail -f logs/stt_service.log  # View logs
python3 test_service.py       # Run tests

# Testing
curl http://localhost:8000/stt/health  # Health check
```

