# TTS Service Setup - Official CosyVoice Implementation

## What Changed?

This service has been **completely refactored** to follow the **official CosyVoice installation guide** from the FunAudioLLM team.

### Previous Issues

The old implementation had several problems:
1. ❌ Used Python venv instead of Conda (official uses Conda)
2. ❌ Incorrect import paths for CosyVoice
3. ❌ Wrong Python version (3.9+ vs official 3.8)
4. ❌ Custom dependency management instead of official requirements.txt
5. ❌ Incorrect model loading API
6. ❌ Non-standard directory structure

### New Implementation

The new implementation follows the official guide exactly:
1. ✅ **Conda environment** with Python 3.8 (as specified)
2. ✅ **Official CosyVoice clone** with proper submodules
3. ✅ **Official dependencies** from CosyVoice/requirements.txt
4. ✅ **Correct import paths** using sitecustomize.py
5. ✅ **Official API calls** for model loading and inference
6. ✅ **ModelScope integration** for automatic model downloads
7. ✅ **Proper speaker support** using list_available_spks()
8. ✅ **Streaming API** following official examples

---

## Installation Process

### System Requirements

- **Conda (Miniconda/Anaconda)** - Required
- **Python 3.8** - Specific version required by CosyVoice
- **FFmpeg, libsndfile, sox** - Audio libraries
- **Git with LFS** - For repository cloning
- **CUDA 11.8+** - Optional, for GPU acceleration

### Quick Setup

```bash
# 1. Install Conda if not already installed
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 2. Run automated setup
cd tts_service
./setup.sh

# 3. Start service
./start_service.sh

# 4. Test
curl http://localhost:8002/health
```

### What setup.sh Does

The setup script automates the official installation process:

```bash
# 1. Check Conda installation
✓ Verify conda is available

# 2. Install system dependencies
✓ ffmpeg, libsndfile, sox, git-lfs

# 3. Create conda environment
✓ conda create -n cosyvoice python=3.8

# 4. Install PyTorch
✓ PyTorch 2.0.1 with CUDA 11.8 (or CPU)

# 5. Clone CosyVoice
✓ git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git

# 6. Install CosyVoice dependencies
✓ pip install -r CosyVoice/requirements.txt

# 7. Configure Python paths
✓ Setup sitecustomize.py for imports

# 8. Install service dependencies
✓ FastAPI, uvicorn, websockets, pydantic

# 9. Test installation
✓ Verify all imports work correctly
```

---

## Architecture Overview

### Directory Structure

```
tts_service/
├── CosyVoice/                    # Official CosyVoice repository (cloned)
│   ├── cosyvoice/                # Main CosyVoice package
│   ├── third_party/              # Dependencies (Matcha-TTS, etc.)
│   └── requirements.txt          # Official dependencies
│
├── pretrained_models/            # Downloaded models
│   └── CosyVoice-300M-SFT/      # Default model (~1GB)
│
├── config.py                     # Service configuration
├── tts_server.py                 # FastAPI server
├── synthesis.py                  # CosyVoice integration
├── audio_utils.py                # Audio processing
├── text_processor.py             # Text handling
├── test_client.py                # Test suite
│
├── setup.sh                      # Automated setup script
├── start_service.sh              # Service start script
├── stop_service.sh               # Service stop script
├── activate_env.sh               # Helper to activate conda env
│
└── INSTALLATION.md               # Detailed installation guide
```

### Import Resolution

Python imports are configured via `sitecustomize.py`:

```python
import sys
sys.path.insert(0, '/path/to/CosyVoice')
sys.path.insert(0, '/path/to/CosyVoice/third_party/Matcha-TTS')
```

This allows:
```python
from cosyvoice.cli.cosyvoice import CosyVoice  # ✓ Works
from cosyvoice.utils.file_utils import load_wav  # ✓ Works
```

---

## Model Configuration

### Default Model

**CosyVoice-300M-SFT** (Supervised Fine-Tuned model)
- Size: ~1 GB
- Best for: General purpose TTS
- Language support: Chinese, English, Japanese, Korean, Cantonese
- ModelScope ID: `iic/CosyVoice-300M-SFT`

### Available Speakers (SFT Model)

The SFT model includes built-in speakers:
- `中文女` - Chinese Female
- `中文男` - Chinese Male
- `日语男` - Japanese Male
- `粤语女` - Cantonese Female
- `英文女` - English Female
- `英文男` - English Male
- `韩语女` - Korean Female

### API Usage

Official CosyVoice API calls:

```python
# Load model (official way)
from cosyvoice.cli.cosyvoice import CosyVoice
model = CosyVoice('pretrained_models/CosyVoice-300M-SFT')

# List available speakers
speakers = model.list_available_spks()

# Non-streaming inference (official API)
for audio_chunk in model.inference_sft(text, speaker, stream=False):
    audio = audio_chunk['tts_speech']
    # Process audio...

# Streaming inference (official API)
for audio_chunk in model.inference_sft(text, speaker, stream=True):
    audio = audio_chunk['tts_speech']
    # Stream audio...
```

---

## Migration from Old Setup

If you're migrating from the old setup:

### 1. Clean Old Installation

```bash
# Remove old virtual environment
rm -rf venv/

# Remove old model downloads
rm -rf models/

# Keep your configuration if customized
# Backup config.py changes if any
```

### 2. Install Conda

```bash
# Download and install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
```

### 3. Run New Setup

```bash
# Run the new setup script
./setup.sh

# This will:
# - Create conda environment 'cosyvoice'
# - Install all dependencies properly
# - Clone official CosyVoice
# - Configure imports correctly
```

### 4. Update Service Scripts

The service scripts now use conda activation:

```bash
# Old way (don't use):
source venv/bin/activate

# New way:
source activate_env.sh
# or
conda activate cosyvoice
```

### 5. Configuration Changes

Update `config.py` if you made custom changes:

```python
# Old config
model_path: str = "iic/CosyVoice2-0.5B"  # Remote ID

# New config
model_path: str = "pretrained_models/CosyVoice-300M-SFT"  # Local path
modelscope_model_id: str = "iic/CosyVoice-300M-SFT"  # For download
```

---

## Verification Checklist

After setup, verify everything works:

### ✅ Environment Check

```bash
# Activate environment
source activate_env.sh

# Check Python version
python --version
# Should show: Python 3.8.x

# Check conda environment
conda info --envs
# Should show: cosyvoice (active)
```

### ✅ Import Check

```bash
# Test CosyVoice import
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('✓ OK')"

# Test all imports
python -c "
from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torch
import fastapi
print('✓ All imports successful')
"
```

### ✅ Service Check

```bash
# Start service
./start_service.sh

# Check health
curl http://localhost:8002/health

# Expected output:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "service": "CosyVoice2 TTS",
#   "model_name": "CosyVoice-300M-SFT",
#   ...
# }
```

### ✅ Synthesis Check

```bash
# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test"}'

# Should return JSON with audio_base64
```

### ✅ Speakers Check

```bash
# List available voices
curl http://localhost:8002/voices

# Expected output:
# {
#   "voices": [
#     {"id": "中文女", "name": "中文女", ...},
#     {"id": "中文男", "name": "中文男", ...},
#     ...
#   ]
# }
```

---

## Common Issues & Solutions

### Issue: "Conda command not found"

**Solution:**
```bash
# Add conda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"

# Or reinstall conda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### Issue: "CosyVoice import fails"

**Solution:**
```bash
# Check if CosyVoice directory exists
ls -la CosyVoice/

# Re-run setup if missing
./setup.sh

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
# Should include CosyVoice directory
```

### Issue: "Model not found"

**Solution:**
```bash
# Model will download automatically on first run
# Or pre-download:
conda activate cosyvoice
cd CosyVoice
python -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')"
```

### Issue: "Service fails to start"

**Solution:**
```bash
# Check logs
cat tts_service.log

# Verify environment
source activate_env.sh
python tts_server.py  # Run in foreground to see errors
```

---

## Performance Notes

### GPU vs CPU

**With GPU (CUDA):**
- RTF (Real-Time Factor): ~10-20x (depends on GPU)
- Memory: ~2-4 GB VRAM
- Recommended for production

**CPU Only:**
- RTF: ~0.3-0.5x (slower than real-time)
- Memory: ~4-8 GB RAM
- Acceptable for testing/development

### First Run

The first time you run the service:
1. Model downloads from ModelScope (~1 GB)
2. Model loads into memory (~30-60 seconds)
3. Warmup synthesis runs

Subsequent runs are much faster (model already downloaded).

---

## References

- **Official CosyVoice:** https://github.com/FunAudioLLM/CosyVoice
- **ModelScope:** https://www.modelscope.cn/models/iic
- **Installation Guide:** See `INSTALLATION.md`
- **API Guide:** See `CLIENT_API_GUIDE.md`
- **Configuration:** See `CONFIG_REFERENCE.md`

---

## Summary

| Aspect | Old Implementation | New Implementation |
|--------|-------------------|-------------------|
| Environment | Python venv | Conda |
| Python Version | 3.9+ | 3.8 (official) |
| CosyVoice | Separate clone | Official clone with submodules |
| Dependencies | Custom list | Official requirements.txt |
| Imports | Manual PYTHONPATH | sitecustomize.py |
| Model Loading | Custom code | Official API |
| Speakers | Hardcoded | Dynamic from model |
| Inference | Custom implementation | Official inference_sft API |
| Streaming | Custom chunking | Official stream=True API |

The new implementation is **production-ready**, **maintainable**, and follows **official best practices**.

---

**Need help?** Check `INSTALLATION.md` for detailed instructions and troubleshooting.

