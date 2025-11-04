# TTS Service - Quick Start Guide

Get started with the CosyVoice2 TTS Service in 5 minutes!

## 🎯 Overview

This guide will help you:
1. ✅ Install and setup the service
2. ✅ Start the TTS server
3. ✅ Make your first synthesis request
4. ✅ Test streaming synthesis

**Time Required**: ~5 minutes (+ model download time on first run)

---

## Step 1: Installation (2 minutes)

### Quick Install

```bash
# Navigate to service directory
cd tts_service

# Run setup script
./setup.sh
```

The setup script automatically:
- Creates Python virtual environment
- Installs PyTorch (with GPU support if available)
- Installs all dependencies
- Clones CosyVoice2 from GitHub
- Verifies installation

### Expected Output

```
==========================================
CosyVoice2 TTS Service Setup
==========================================
Checking Python version...
Using Python: Python 3.10.x
Creating virtual environment...
Installing PyTorch...
Installing dependencies...
Testing installation...
PyTorch version: 2.1.2
CUDA available: True
==========================================
Setup completed successfully!
==========================================
```

---

## Step 2: Start the Service (30 seconds)

```bash
./start_service.sh
```

### First Run (Model Download)

On first run, CosyVoice2-0.5B model (~500MB) downloads automatically:

```
==========================================
Starting CosyVoice2 TTS Service
==========================================
Starting TTS service on port 8002...

Note: First run will download CosyVoice2-0.5B model (~500MB)
This may take several minutes...

INFO: Loading CosyVoice2 model: CosyVoice2-0.5B
INFO: Downloading model from Hugging Face...
INFO: Model loaded successfully
INFO: Service ready!
INFO: Listening on 0.0.0.0:8002
```

### Subsequent Runs

After first run, startup is fast (~5-10 seconds):

```
INFO: Loading CosyVoice2 model from cache
INFO: Model loaded successfully
INFO: Service ready!
```

### Verify Service is Running

```bash
# Check health
curl http://localhost:8002/health

# Should return:
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "CosyVoice2 TTS",
  "model_name": "CosyVoice2-0.5B",
  "device": "cuda",
  "available_speakers": ["default", ...]
}
```

---

## Step 3: Your First Synthesis (1 minute)

### HTTP API - Simple Synthesis

```bash
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! Welcome to the CosyVoice2 TTS service. This is a test of high-quality speech synthesis."
  }' | python3 -m json.tool
```

**Response:**
```json
{
  "success": true,
  "audio_base64": "UklGRiQAAABXQVZFZm10...",
  "audio_format": "pcm_s16le",
  "text": "Hello! Welcome to...",
  "sample_rate": 24000,
  "audio_duration": 4.5,
  "processing_time": 0.234,
  "realtime_factor": 0.052,
  "speaker": "default"
}
```

### Save Audio to File

```bash
# Using Python
python3 << 'EOF'
import requests
import base64
import wave

response = requests.post('http://localhost:8002/synthesize', json={
    "text": "Hello! This is a test of the text-to-speech service."
})

result = response.json()
audio_bytes = base64.b64decode(result['audio_base64'])

with wave.open('output.wav', 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(24000)
    wav.writeframes(audio_bytes)

print(f"✓ Audio saved to output.wav ({len(audio_bytes)} bytes)")
print(f"  Duration: {result['audio_duration']:.2f}s")
print(f"  Processing: {result['processing_time']:.3f}s")
EOF
```

---

## Step 4: Test Streaming (1 minute)

### Run Test Suite

```bash
./test_client.py
```

This runs comprehensive tests including:
- ✅ Health check
- ✅ Configuration retrieval
- ✅ Voice listing
- ✅ HTTP synthesis
- ✅ WebSocket streaming (basic)
- ✅ WebSocket streaming (custom config)
- ✅ Control messages
- ✅ Latency testing

**Expected Output:**
```
======================================================================
CosyVoice2 TTS Service - Test Suite v1.0
Comprehensive API Testing
======================================================================

[1/8] Health Check
✓ Health check: {...}

[2/8] Default Configuration
✓ Default config: {...}

[3/8] List Voices
✓ Available voices: 5

[4/8] HTTP Synthesis
✓ HTTP Synthesis Success!
📝 INPUT TEXT: "Hello, world!..."
✓ Saved audio: test_output_http.wav

[5/8] WebSocket Streaming (Basic)
✓ WebSocket connected
🎤 Synthesis started: 150 chars
✅ Audio complete!
✓ Saved audio: test_output_ws_basic.wav

======================================================================
TEST SUMMARY
======================================================================
Health Check.......................................... ✓ PASSED
Get Default Config.................................... ✓ PASSED
List Voices........................................... ✓ PASSED
HTTP Synthesis........................................ ✓ PASSED
WebSocket Basic....................................... ✓ PASSED
WebSocket Custom...................................... ✓ PASSED
Control Messages...................................... ✓ PASSED
Streaming Latency..................................... ✓ PASSED

✓ Total: 8/8 tests passed
======================================================================
```

---

## 🎨 Quick Examples

### Example 1: Different Voice Speeds

```python
import requests

speeds = [0.8, 1.0, 1.3]
for speed in speeds:
    response = requests.post('http://localhost:8002/synthesize', json={
        "text": "Testing different speech speeds.",
        "voice_config": {"speed": speed}
    })
    # Save each version...
```

### Example 2: WebSocket Streaming

```python
import asyncio
import websockets
import json

async def stream_synthesis():
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Send text
        await ws.send(json.dumps({
            "type": "text",
            "text": "This is streaming synthesis!"
        }))
        
        # Receive audio chunks
        audio_chunks = []
        while True:
            msg = await ws.recv()
            if isinstance(msg, bytes):
                audio_chunks.append(msg)
            else:
                data = json.loads(msg)
                if data['type'] == 'audio_complete':
                    break
        
        print(f"Received {len(audio_chunks)} audio chunks")

asyncio.run(stream_synthesis())
```

### Example 3: Low-Latency Streaming

```python
import asyncio
import websockets
import json

async def low_latency_stream():
    async with websockets.connect('ws://localhost:8002/stream') as ws:
        # Configure for low latency
        await ws.send(json.dumps({
            "type": "config",
            "streaming": {
                "flush_threshold": 1,  # Flush immediately
                "optimize_streaming_latency": 4  # Max speed
            }
        }))
        
        await ws.recv()  # Wait for ready
        
        # Stream text incrementally
        sentences = [
            "First sentence.",
            "Second sentence.",
            "Third sentence."
        ]
        
        for sentence in sentences:
            await ws.send(json.dumps({
                "type": "text",
                "text": sentence
            }))
            
            # Receive audio immediately
            while True:
                msg = await ws.recv()
                if isinstance(msg, bytes):
                    print(f"Got audio: {len(msg)} bytes")
                else:
                    data = json.loads(msg)
                    if data['type'] == 'audio_complete':
                        break

asyncio.run(low_latency_stream())
```

---

## 🎛️ Service Management

### Check Service Status

```bash
./tts_manager.sh status
```

### View Logs

```bash
./tts_manager.sh logs
```

### Stop Service

```bash
./tts_manager.sh stop
```

### Restart Service

```bash
./tts_manager.sh restart
```

---

## 🔧 Common Configurations

### High Quality (Best Audio Quality)

```json
{
  "synthesis": {
    "stability": 0.7,
    "similarity_boost": 0.85,
    "temperature": 0.5
  },
  "streaming": {
    "optimize_streaming_latency": 0
  }
}
```

### Low Latency (Fastest Response)

```json
{
  "streaming": {
    "flush_threshold": 1,
    "optimize_streaming_latency": 4,
    "buffer_size": 1
  }
}
```

### Balanced (Good Quality + Speed)

```json
{
  "synthesis": {
    "stability": 0.6,
    "temperature": 0.7
  },
  "streaming": {
    "flush_threshold": 2,
    "optimize_streaming_latency": 2
  }
}
```

---

## ❓ Troubleshooting Quick Fixes

### Service won't start
```bash
# Re-run setup
./setup.sh

# Check logs
cat tts_service.log
```

### Model download fails
```bash
# Clear cache and retry
rm -rf models/
./start_service.sh
```

### CUDA out of memory
```bash
# Force CPU mode
export CUDA_VISIBLE_DEVICES=""
./start_service.sh
```

### Port already in use
```bash
# Check what's using port 8002
lsof -i :8002

# Kill existing service
./tts_manager.sh stop
```

---

## 📚 Next Steps

Now that you have the service running:

1. 📖 Read [CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md) for complete API reference
2. ⚙️ Explore [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) for all configuration options
3. 🔍 Check [README.md](README.md) for architecture and advanced features

---

## 🎉 You're Ready!

You now have a production-ready TTS service running!

**Service URL**: `http://localhost:8002`

**WebSocket URL**: `ws://localhost:8002/stream`

**Health Check**: `curl http://localhost:8002/health`

---

**Questions?** Check the main README or documentation files for detailed guides.

