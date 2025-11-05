# CosyVoice TTS Service - Installation Guide

Complete installation guide following the **official CosyVoice documentation**.

Official Repository: https://github.com/FunAudioLLM/CosyVoice

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Manual Installation](#manual-installation-alternative)
5. [Model Download](#model-download)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Conda (Miniconda or Anaconda)**
   - Required for Python environment management
   - Download: https://docs.conda.io/en/latest/miniconda.html

2. **Git and Git LFS**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install git git-lfs
   
   # macOS
   brew install git git-lfs
   
   # Initialize Git LFS
   git lfs install
   ```

3. **System Libraries**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y ffmpeg libsndfile1 sox
   
   # macOS
   brew install ffmpeg libsndfile sox
   ```

4. **NVIDIA GPU (Optional but Recommended)**
   - For GPU acceleration
   - Requires CUDA 11.8 or compatible version
   - Check: `nvidia-smi`

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8 GB | 16 GB+ |
| **Disk Space** | 5 GB | 10 GB+ |
| **GPU VRAM** | - | 4 GB+ (optional) |
| **Python** | 3.8 | 3.8 |
| **OS** | Linux, macOS | Ubuntu 20.04+ |

---

## Installation Steps

### Automated Installation (Recommended)

The automated setup script follows the official CosyVoice installation process:

```bash
# Navigate to TTS service directory
cd tts_service

# Run setup script
./setup.sh
```

The script will:
1. ✅ Check for Conda installation
2. ✅ Install system dependencies (ffmpeg, libsndfile, sox)
3. ✅ Create conda environment `cosyvoice` with Python 3.8
4. ✅ Install PyTorch with CUDA support (if GPU available)
5. ✅ Clone official CosyVoice repository
6. ✅ Install CosyVoice dependencies from official requirements.txt
7. ✅ Configure Python paths for imports
8. ✅ Test installation

**First Time Setup:** Expected time: 10-15 minutes

### Quick Start After Installation

```bash
# Activate environment
source activate_env.sh

# Start service
./start_service.sh

# Test service
curl http://localhost:8002/health
```

---

## Manual Installation (Alternative)

If you prefer to install manually or the automated script fails:

### Step 1: Install Conda

```bash
# Download Miniconda (Linux)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Download Miniconda (macOS Intel)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Download Miniconda (macOS Apple Silicon)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# Follow installation prompts
# Restart shell after installation
```

### Step 2: Create Conda Environment

```bash
# Create environment with Python 3.8 (official requirement)
conda create -n cosyvoice python=3.8 -y

# Activate environment
conda activate cosyvoice
```

### Step 3: Install PyTorch

```bash
# For CUDA 11.8 (GPU)
pip install torch==2.0.1 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

# For CPU only
pip install torch==2.0.1 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
```

### Step 4: Clone CosyVoice Repository

```bash
# Navigate to tts_service directory
cd tts_service

# Clone official repository with submodules
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git

# If you already cloned without --recursive:
cd CosyVoice
git submodule update --init --recursive
cd ..
```

### Step 5: Install CosyVoice Dependencies

```bash
# Install from official requirements.txt
cd CosyVoice
pip install -r requirements.txt
cd ..
```

### Step 6: Install Service Dependencies

```bash
# Install FastAPI and service dependencies
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 websockets==12.0
pip install pydantic==2.5.3 python-multipart==0.0.6 requests==2.31.0
```

### Step 7: Configure Python Paths

```bash
# Get the absolute path
COSYVOICE_PATH="$(pwd)/CosyVoice"

# Add to conda environment
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")

# Create sitecustomize.py
cat > "${SITE_PACKAGES}/sitecustomize.py" << EOF
import sys
sys.path.insert(0, '${COSYVOICE_PATH}')
sys.path.insert(0, '${COSYVOICE_PATH}/third_party/Matcha-TTS')
EOF
```

### Step 8: Verify Installation

```bash
# Test imports
python << 'EOF'
from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torch
print("✓ CosyVoice imports successful")
print(f"✓ PyTorch: {torch.__version__}")
print(f"✓ CUDA available: {torch.cuda.is_available()}")
EOF
```

---

## Model Download

Models will be downloaded automatically from ModelScope on first use. You can also pre-download:

### Available Models

| Model | Size | Description | Model ID |
|-------|------|-------------|----------|
| **CosyVoice-300M-SFT** | ~1 GB | Supervised Fine-Tuned (Recommended) | `iic/CosyVoice-300M-SFT` |
| CosyVoice-300M | ~1 GB | Base model | `iic/CosyVoice-300M` |
| CosyVoice-300M-Instruct | ~1 GB | Instruct model | `iic/CosyVoice-300M-Instruct` |
| CosyVoice2-0.5B | ~500 MB | Latest, smaller, faster | `iic/CosyVoice2-0.5B` |

### Pre-download Model (Optional)

```bash
# Activate environment
conda activate cosyvoice

# Create models directory
mkdir -p pretrained_models

# Download CosyVoice-300M-SFT (recommended)
cd CosyVoice
python << 'EOF'
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')
print("✓ Model downloaded successfully")
EOF
cd ..
```

**Model Location:** Models are stored in `pretrained_models/` directory.

---

## Verification

### Test CosyVoice Import

```bash
conda activate cosyvoice
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('✓ CosyVoice OK')"
```

### Test Service

```bash
# Start service
./start_service.sh

# In another terminal:
# Health check
curl http://localhost:8002/health

# List available voices
curl http://localhost:8002/voices

# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test."}'
```

### Run Test Suite

```bash
conda activate cosyvoice
python test_client.py
```

---

## Troubleshooting

### Issue: Conda not found

```bash
# Make sure conda is in PATH
export PATH="$HOME/miniconda3/bin:$PATH"

# Or add to ~/.bashrc or ~/.zshrc:
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: CosyVoice import fails

```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Should include CosyVoice directory
# If not, recreate sitecustomize.py (see Step 7)

# Or manually add to PYTHONPATH
export PYTHONPATH="/path/to/tts_service/CosyVoice:$PYTHONPATH"
```

### Issue: Model download fails

```bash
# Option 1: Manual download
cd CosyVoice
python -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')"

# Option 2: Check network/proxy settings
export HF_ENDPOINT=https://hf-mirror.com  # If accessing from restricted regions

# Option 3: Download from alternative source
# Visit: https://www.modelscope.cn/models/iic/CosyVoice-300M-SFT
```

### Issue: CUDA out of memory

```bash
# Use CPU instead
export CUDA_VISIBLE_DEVICES=""

# Or reduce batch size in config.py
# Or use smaller model (CosyVoice2-0.5B)
```

### Issue: Missing system libraries

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential pkg-config ffmpeg libsndfile1-dev sox

# macOS
brew install pkg-config ffmpeg libsndfile sox
```

### Issue: Git submodules not initialized

```bash
cd CosyVoice
git submodule update --init --recursive
cd ..
```

### Issue: Service starts but doesn't respond

```bash
# Check logs
tail -f tts_service.log

# Check if port is in use
lsof -i :8002

# Try different port in config.py:
# port: int = 8003
```

---

## Environment Management

### Activate Environment

```bash
# Method 1: Using helper script
source activate_env.sh

# Method 2: Direct conda activation
conda activate cosyvoice
```

### Deactivate Environment

```bash
conda deactivate
```

### Delete Environment (Clean Reinstall)

```bash
conda env remove -n cosyvoice
# Then run setup.sh again
```

### Update CosyVoice

```bash
conda activate cosyvoice
cd CosyVoice
git pull
git submodule update --init --recursive
pip install -r requirements.txt
cd ..
```

---

## Development Setup

For development and debugging:

```bash
# Activate environment
conda activate cosyvoice

# Install development tools
pip install ipython jupyter pytest black flake8

# Run service in foreground (with logs)
python tts_server.py

# Run with debug logging
# Edit config.py: log_level = "debug"
```

---

## Production Deployment

For production use:

1. **Use a process manager:**
   ```bash
   # Install supervisor
   sudo apt-get install supervisor
   
   # Create supervisor config (see tts_manager.sh)
   ```

2. **Set up reverse proxy (Nginx):**
   ```nginx
   server {
       listen 80;
       location /tts/ {
           proxy_pass http://localhost:8002/;
       }
   }
   ```

3. **Configure firewall:**
   ```bash
   sudo ufw allow 8002/tcp
   ```

4. **Monitor logs:**
   ```bash
   tail -f tts_service.log
   ```

---

## References

- **Official CosyVoice GitHub:** https://github.com/FunAudioLLM/CosyVoice
- **ModelScope Models:** https://www.modelscope.cn/models/iic
- **CosyVoice Paper:** https://arxiv.org/abs/2407.05407
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

## Support

For issues specific to:
- **CosyVoice model:** Check https://github.com/FunAudioLLM/CosyVoice/issues
- **This service:** Check service logs and configuration
- **Installation:** Follow troubleshooting steps above

---

**Last Updated:** Based on CosyVoice v1.0 (2024)

