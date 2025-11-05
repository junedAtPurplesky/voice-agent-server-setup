# Server Setup Guide - CosyVoice TTS Service

Complete guide for setting up the TTS service on your server following the official CosyVoice installation.

---

## Quick Server Setup

For a fresh server setup, follow these steps in order:

### Step 1: Install Conda

```bash
# Download Miniconda (Linux x86_64)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install
bash Miniconda3-latest-Linux-x86_64.sh

# Follow prompts:
# - Accept license (yes)
# - Confirm installation location
# - Allow conda init (yes)

# Restart shell to activate conda
exec bash

# Verify installation
conda --version
```

### Step 2: Install System Dependencies

```bash
# Update package manager
sudo apt-get update

# Install required system libraries
sudo apt-get install -y \
    git \
    git-lfs \
    ffmpeg \
    libsndfile1 \
    sox \
    build-essential

# Initialize Git LFS
git lfs install

# Verify installations
git --version
git lfs version
ffmpeg -version
```

### Step 3: Navigate to TTS Service

```bash
# Go to your project directory
cd /path/to/voice-agent-server-setup/tts_service

# Verify files exist
ls -la setup.sh
```

### Step 4: Run Automated Setup

```bash
# Make setup script executable (if needed)
chmod +x setup.sh

# Run setup script
./setup.sh
```

**What happens during setup:**
1. Checks Conda is installed
2. Creates `cosyvoice` conda environment with Python 3.8
3. Installs PyTorch with CUDA support (if GPU available)
4. Clones official CosyVoice repository
5. Installs all dependencies
6. Configures Python paths
7. Tests installation

**Expected Duration:** 10-15 minutes (depending on internet speed)

### Step 5: Start the Service

```bash
# Make start script executable (if needed)
chmod +x start_service.sh

# Start service
./start_service.sh
```

The service will:
- Activate conda environment
- Download model on first run (~1GB, may take 5-10 minutes)
- Start server on port 8002
- Run in background

### Step 6: Verify Service

```bash
# Check health
curl http://localhost:8002/health

# List available voices
curl http://localhost:8002/voices

# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test of the CosyVoice text-to-speech service."}'
```

---

## Server Requirements

### Minimum Requirements

- **OS:** Ubuntu 20.04+ or similar Linux distribution
- **RAM:** 8 GB
- **Disk:** 10 GB free space
- **CPU:** 4+ cores
- **Network:** Stable internet for model download

### Recommended Requirements

- **OS:** Ubuntu 22.04 LTS
- **RAM:** 16 GB or more
- **Disk:** 20 GB+ free space
- **CPU:** 8+ cores
- **GPU:** NVIDIA GPU with 4GB+ VRAM (RTX 2060 or better)
- **CUDA:** 11.8 or later (if using GPU)

### GPU Setup (Optional but Recommended)

If you have an NVIDIA GPU:

```bash
# Check NVIDIA driver
nvidia-smi

# Expected output shows GPU info and CUDA version
# If command not found, install NVIDIA drivers:
# https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

# Verify CUDA version
nvcc --version

# CUDA 11.8+ is recommended
```

---

## Detailed Setup Steps

### 1. Pre-Setup Verification

Before running setup, ensure:

```bash
# Check if conda is available
which conda
# Should output: /home/username/miniconda3/bin/conda

# Check if git-lfs is installed
git lfs version
# Should output: git-lfs/x.x.x

# Check disk space
df -h .
# Ensure at least 10GB free

# Check memory
free -h
# Ensure at least 8GB RAM
```

### 2. Clone/Update Project

```bash
# If you haven't cloned the project yet:
git clone <your-repo-url>
cd voice-agent-server-setup/tts_service

# If project already exists, pull latest changes:
cd voice-agent-server-setup/tts_service
git pull
```

### 3. Run Setup Script

```bash
# Review setup script first (optional)
cat setup.sh

# Run setup
./setup.sh

# Monitor output for any errors
# Setup should complete with "✓ SETUP COMPLETED SUCCESSFULLY!"
```

**If setup fails**, check:
- Conda is properly installed
- Internet connection is stable
- Disk space is sufficient
- All system dependencies are installed

### 4. Verify Conda Environment

```bash
# List conda environments
conda env list

# Should show 'cosyvoice' environment
# Example output:
# cosyvoice                /home/username/miniconda3/envs/cosyvoice

# Activate environment
source activate_env.sh
# or
conda activate cosyvoice

# Verify Python version
python --version
# Should output: Python 3.8.x

# Test CosyVoice import
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('✓ CosyVoice OK')"
# Should output: ✓ CosyVoice OK
```

### 5. Pre-Download Model (Optional)

To avoid long wait on first startup, pre-download the model:

```bash
# Activate environment
conda activate cosyvoice

# Create models directory
mkdir -p pretrained_models

# Download model
cd CosyVoice
python << 'EOF'
from modelscope import snapshot_download
print("Downloading CosyVoice-300M-SFT model...")
snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')
print("✓ Model downloaded successfully")
EOF
cd ..

# Verify model files
ls -lh pretrained_models/CosyVoice-300M-SFT/
```

### 6. Configure Service (Optional)

Edit configuration if needed:

```bash
# Edit config.py for custom settings
nano config.py

# Key settings:
# - port: Change service port (default 8002)
# - host: Change bind address (default 0.0.0.0)
# - log_level: Change logging verbosity (info/debug)
# - model_path: Change model location
```

### 7. Start Service

```bash
# Start in background
./start_service.sh

# Service will:
# 1. Activate conda environment
# 2. Check CosyVoice installation
# 3. Download model if not present
# 4. Start server on port 8002
# 5. Run in background with PID saved to .service.pid

# Check if service started
cat .service.pid
ps aux | grep tts_server
```

### 8. Monitor Logs

```bash
# View real-time logs
tail -f tts_service.log

# Search for errors
grep ERROR tts_service.log

# View last 50 lines
tail -50 tts_service.log
```

---

## Service Management

### Start Service

```bash
./start_service.sh

# Or using manager script:
./tts_manager.sh start
```

### Stop Service

```bash
./stop_service.sh

# Or using manager script:
./tts_manager.sh stop
```

### Restart Service

```bash
# Stop then start
./stop_service.sh && ./start_service.sh

# Or using manager script:
./tts_manager.sh restart
```

### Check Status

```bash
# Using manager script:
./tts_manager.sh status

# Or manually:
if [ -f .service.pid ]; then
    PID=$(cat .service.pid)
    ps -p $PID > /dev/null && echo "Running (PID: $PID)" || echo "Not running"
else
    echo "Not running"
fi
```

### View Logs

```bash
# Real-time logs
tail -f tts_service.log

# Last 100 lines
tail -100 tts_service.log

# Using manager script:
./tts_manager.sh logs
```

---

## Firewall Configuration

### Open Port for Service

```bash
# Using ufw (Ubuntu)
sudo ufw allow 8002/tcp
sudo ufw reload

# Verify
sudo ufw status

# Using firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8002/tcp
sudo firewall-cmd --reload
```

### Test from Remote Machine

```bash
# From another machine on the network
curl http://<server-ip>:8002/health

# Example:
curl http://192.168.1.100:8002/health
```

---

## Production Deployment

### Using Systemd (Recommended)

Create a systemd service for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/cosyvoice-tts.service
```

Add the following content:

```ini
[Unit]
Description=CosyVoice TTS Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/tts_service
Environment="PATH=/home/your-username/miniconda3/envs/cosyvoice/bin:/usr/bin"
ExecStart=/home/your-username/miniconda3/envs/cosyvoice/bin/python tts_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `your-username` and `/path/to/tts_service` with actual values.

Enable and start service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable cosyvoice-tts

# Start service
sudo systemctl start cosyvoice-tts

# Check status
sudo systemctl status cosyvoice-tts

# View logs
sudo journalctl -u cosyvoice-tts -f
```

### Using Nginx Reverse Proxy

Set up Nginx as reverse proxy:

```bash
# Install Nginx
sudo apt-get install nginx

# Create config
sudo nano /etc/nginx/sites-available/tts-service
```

Add configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /tts/ {
        proxy_pass http://localhost:8002/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Enable configuration:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/tts-service /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Certificate will auto-renew
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
cat tts_service.log
```

**Common issues:**

1. **Conda environment not found**
   ```bash
   # Verify environment exists
   conda env list
   
   # If missing, re-run setup
   ./setup.sh
   ```

2. **CosyVoice import fails**
   ```bash
   # Test manually
   conda activate cosyvoice
   python -c "from cosyvoice.cli.cosyvoice import CosyVoice"
   
   # If fails, check CosyVoice directory
   ls -la CosyVoice/
   
   # Re-clone if needed
   rm -rf CosyVoice
   git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
   ```

3. **Model download fails**
   ```bash
   # Pre-download manually
   conda activate cosyvoice
   cd CosyVoice
   python -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')"
   ```

4. **Port already in use**
   ```bash
   # Check what's using port 8002
   sudo lsof -i :8002
   
   # Kill process if needed
   sudo kill -9 <PID>
   
   # Or change port in config.py
   ```

### CUDA Errors

```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# If False but you have GPU:
# 1. Check NVIDIA driver
nvidia-smi

# 2. Reinstall PyTorch with CUDA
conda activate cosyvoice
pip install torch==2.0.1 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

# 3. Or force CPU mode
export CUDA_VISIBLE_DEVICES=""
```

### Memory Issues

```bash
# Check memory usage
free -h

# If low memory, use CPU mode
export CUDA_VISIBLE_DEVICES=""

# Or increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Server Maintenance

### Update Service

```bash
# Stop service
./stop_service.sh

# Pull latest changes
git pull

# Update CosyVoice
cd CosyVoice
git pull
git submodule update --init --recursive
cd ..

# Update dependencies
conda activate cosyvoice
cd CosyVoice
pip install -r requirements.txt
cd ..

# Restart service
./start_service.sh
```

### Monitor Performance

```bash
# CPU usage
top -p $(cat .service.pid)

# Memory usage
ps aux | grep tts_server | awk '{print $6}'

# GPU usage (if applicable)
watch -n 1 nvidia-smi
```

### Backup Configuration

```bash
# Backup custom settings
tar -czf tts-backup-$(date +%Y%m%d).tar.gz \
    config.py \
    pretrained_models/ \
    tts_service.log

# Restore if needed
tar -xzf tts-backup-YYYYMMDD.tar.gz
```

---

## Summary Checklist

- [ ] Conda installed and working
- [ ] System dependencies installed (git, ffmpeg, etc.)
- [ ] setup.sh completed successfully
- [ ] Conda environment 'cosyvoice' created
- [ ] CosyVoice imports work
- [ ] Model downloaded
- [ ] Service starts without errors
- [ ] Health endpoint responds
- [ ] Synthesis test successful
- [ ] Firewall configured (if needed)
- [ ] Systemd service configured (production)
- [ ] Logs are accessible

---

## Quick Reference

| Task | Command |
|------|---------|
| Start service | `./start_service.sh` |
| Stop service | `./stop_service.sh` |
| View logs | `tail -f tts_service.log` |
| Check status | `./tts_manager.sh status` |
| Activate env | `conda activate cosyvoice` |
| Health check | `curl http://localhost:8002/health` |
| List voices | `curl http://localhost:8002/voices` |

---

For more details, see:
- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide
- **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** - What changed and why
- **[CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md)** - API usage examples
- **[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)** - Configuration options

