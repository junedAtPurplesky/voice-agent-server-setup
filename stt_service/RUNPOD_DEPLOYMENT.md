# STT Service - RunPod Deployment Guide

## 🚀 Quick Start

This guide will help you deploy the STT service on RunPod without Docker.

## Prerequisites

- RunPod account with GPU instance
- SSH access to RunPod instance
- Basic terminal knowledge

## Deployment Steps

### 1. Connect to RunPod Instance

```bash
# SSH into your RunPod instance
ssh root@your-runpod-instance-ip
```

### 2. Clone or Upload the Code

```bash
# Option A: Clone from repository
cd /workspace
git clone <your-repo-url> stt_service
cd stt_service

# Option B: Upload via SCP
# From your local machine:
# scp -r stt_service root@your-runpod-instance-ip:/workspace/
```

### 3. Run Setup Script

```bash
cd /workspace/stt_service
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Check system requirements
- Install Python dependencies
- Install system dependencies (ffmpeg, libsndfile1)
- Create necessary directories
- Generate default .env configuration

### 4. Configure Service

Edit the `.env` file to customize your configuration:

```bash
nano .env
```

Key settings to review:
```bash
# Model (adjust based on your GPU)
STT_MODEL_NAME=large-v3-turbo  # or base, small, medium for less VRAM

# Device
STT_DEVICE=cuda  # or cpu if no GPU

# API Security
STT_API_KEY=your_secure_api_key_here  # CHANGE THIS!

# Port
STT_PORT=8000  # Change if needed
```

### 5. Start the Service

```bash
./start.sh
```

Expected output:
```
🚀 Starting STT Service...
✅ Service started successfully!
   PID: 12345
   Host: 0.0.0.0
   Port: 8000
```

### 6. Verify Service

```bash
./status.sh
```

Or test manually:
```bash
curl http://localhost:8000/stt/health
```

### 7. Test the Service

```bash
python3 test_service.py
```

## Service Management

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
# Real-time logs
tail -f logs/stt_service.log

# Last 100 lines
tail -n 100 logs/stt_service.log

# Search for errors
grep ERROR logs/stt_service.log
```

## API Usage

### Health Check
```bash
curl http://your-runpod-ip:8000/stt/health
```

### File Transcription
```bash
curl -X POST "http://your-runpod-ip:8000/stt/transcribe" \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@audio.wav" \
  -F "language=hi"
```

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://your-runpod-ip:8000/stt/ws/realtime?token=your_api_key&language=hi');
```

### WebSocket (Full-duplex with VAD)
```javascript
const ws = new WebSocket('ws://your-runpod-ip:8000/stt/ws/fullduplex?token=your_api_key&language=hi');
```

## Exposing Service Externally

### Option 1: RunPod Public Port

1. In RunPod dashboard, add public port mapping:
   - Container Port: 8000
   - Protocol: HTTP

2. Access via: `https://your-pod-id-8000.proxy.runpod.net/stt/`

### Option 2: ngrok (for testing)

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
./ngrok config add-authtoken YOUR_TOKEN

# Expose service
./ngrok http 8000
```

### Option 3: Custom Domain

Set up reverse proxy using nginx or caddy (see advanced configuration).

## Auto-Start on Boot

Create a systemd service (if RunPod supports it):

```bash
sudo nano /etc/systemd/system/stt-service.service
```

```ini
[Unit]
Description=STT Service
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/workspace/stt_service
ExecStart=/workspace/stt_service/start.sh
ExecStop=/workspace/stt_service/stop.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable stt-service
sudo systemctl start stt-service
```

## Troubleshooting

### Service Won't Start

1. Check logs:
```bash
cat logs/stt_service.log
```

2. Check if port is in use:
```bash
lsof -i :8000
# or
netstat -tuln | grep 8000
```

3. Check Python dependencies:
```bash
pip3 list | grep -E "fastapi|uvicorn|whisper"
```

### CUDA Not Available

If CUDA is not detected:

1. Check CUDA installation:
```bash
nvidia-smi
python3 -c "import torch; print(torch.cuda.is_available())"
```

2. Switch to CPU mode:
```bash
# Edit .env
STT_DEVICE=cpu
STT_COMPUTE_TYPE=float32
```

### Model Download Issues

If model download fails:

1. Manually download model:
```bash
python3 -c "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu')"
```

2. Set model cache directory:
```bash
export HF_HOME=/workspace/models
# Add to .env:
STT_DOWNLOAD_ROOT=/workspace/models
```

### Memory Issues

If running out of memory:

1. Use smaller model:
```bash
# .env
STT_MODEL_NAME=base  # or tiny, small
```

2. Reduce workers:
```bash
# .env
STT_WORKERS=1
```

3. Monitor memory:
```bash
watch -n 1 nvidia-smi
```

## Performance Optimization

### GPU Optimization

```bash
# .env for A100/A6000
STT_COMPUTE_TYPE=float16
STT_MODEL_NAME=large-v3-turbo

# .env for RTX 3090/4090
STT_COMPUTE_TYPE=int8
STT_MODEL_NAME=large-v3-turbo

# .env for lower-end GPUs
STT_COMPUTE_TYPE=int8
STT_MODEL_NAME=medium
```

### CPU Optimization (No GPU)

```bash
# .env
STT_DEVICE=cpu
STT_COMPUTE_TYPE=int8
STT_MODEL_NAME=base
```

## Monitoring

### System Resources
```bash
# CPU and Memory
htop

# GPU
watch -n 1 nvidia-smi

# Disk usage
df -h
```

### Service Metrics
```bash
# Request count
grep "POST /stt/transcribe" logs/stt_service.log | wc -l

# Error count
grep ERROR logs/stt_service.log | wc -l

# Active connections
./status.sh
```

## Security Considerations

1. **Change default API key**:
```bash
# Generate secure key
openssl rand -hex 32
# Update .env
STT_API_KEY=your_new_secure_key
```

2. **Firewall rules**:
```bash
# Allow only specific IPs
sudo ufw allow from YOUR_IP to any port 8000
```

3. **Use HTTPS**: Set up reverse proxy with SSL certificate

4. **Rate limiting**: Configure in application or use nginx

## Backup and Restore

### Backup
```bash
tar -czf stt_service_backup.tar.gz \
  /workspace/stt_service/.env \
  /workspace/stt_service/logs \
  /workspace/stt_service/models
```

### Restore
```bash
tar -xzf stt_service_backup.tar.gz -C /
```

## Updating the Service

```bash
cd /workspace/stt_service

# Stop service
./stop.sh

# Pull latest code
git pull origin main

# Update dependencies
pip3 install -r requirements.txt --upgrade

# Start service
./start.sh
```

## Support

For issues and questions:
- Check logs: `tail -f logs/stt_service.log`
- Run status check: `./status.sh`
- Test service: `python3 test_service.py`
- Review documentation: `README.md`

## Quick Command Reference

```bash
# Setup
./setup.sh

# Start/Stop/Restart
./start.sh
./stop.sh
./restart.sh

# Monitor
./status.sh
tail -f logs/stt_service.log

# Test
python3 test_service.py
curl http://localhost:8000/stt/health

# Debug
grep ERROR logs/stt_service.log
ps aux | grep uvicorn
netstat -tuln | grep 8000
```

