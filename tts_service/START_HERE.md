# 🚀 START HERE - CosyVoice TTS Service

## ⚠️ IMPORTANT CHANGES

**This TTS service has been completely refactored to follow the official CosyVoice installation guide.**

If you're seeing configuration or linking problems, it's because the previous setup didn't follow the official installation process. This has been fixed!

---

## 📖 What You Need to Know

### The Problem (What You Were Experiencing)

Your previous setup had these issues:
1. ❌ Used Python venv instead of Conda (official requires Conda)
2. ❌ Wrong Python version (3.9+ vs official requirement of 3.8)
3. ❌ Incorrect CosyVoice import paths
4. ❌ Custom dependencies instead of official requirements.txt
5. ❌ Non-standard model loading

**Result:** Configuration errors, linking problems, import failures

### The Solution (What Changed)

Everything now follows the **official CosyVoice documentation** exactly:
1. ✅ Uses Conda with Python 3.8
2. ✅ Official CosyVoice repository clone
3. ✅ Official dependencies from requirements.txt
4. ✅ Correct import paths via sitecustomize.py
5. ✅ Official API calls (inference_sft)
6. ✅ Proper model management via ModelScope

**Result:** Everything works as the CosyVoice team intended

---

## 🎯 Quick Setup (3 Steps)

### Step 1: Install Conda

**Required:** You MUST have Conda (Miniconda or Anaconda) installed.

```bash
# Check if already installed
conda --version

# If not installed:
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
exec bash  # Restart shell
```

### Step 2: Run Setup

```bash
cd tts_service
./setup.sh
```

This will automatically:
- Create conda environment with Python 3.8
- Install PyTorch with CUDA support (if GPU available)
- Clone official CosyVoice repository
- Install all dependencies correctly
- Configure Python imports
- Test installation

**Duration:** 10-15 minutes

### Step 3: Start Service

```bash
./start_service.sh
```

First startup will download the model (~1GB, takes 5-10 minutes).

**That's it!** Your service is now running on port 8002.

---

## 🧪 Verify It Works

```bash
# Health check
curl http://localhost:8002/health

# List available voices
curl http://localhost:8002/voices

# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test!"}'
```

If all three commands work, you're good to go! ✅

---

## 📚 Documentation Overview

Depending on what you need, read:

| Document | When to Read |
|----------|--------------|
| **[SERVER_SETUP_GUIDE.md](SERVER_SETUP_GUIDE.md)** | Setting up on a new server |
| **[INSTALLATION.md](INSTALLATION.md)** | Detailed installation steps |
| **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** | Understanding what changed |
| **[CLIENT_API_GUIDE.md](CLIENT_API_GUIDE.md)** | Using the API |
| **[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)** | Configuring the service |
| **[README.md](README.md)** | Full overview |

---

## 🔧 If You Had Previous Setup

### Clean Old Installation

```bash
# Remove old virtual environment
rm -rf venv/

# Remove old models (will re-download)
rm -rf models/
```

### Install Conda (if not installed)

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
exec bash
```

### Run New Setup

```bash
./setup.sh
```

This installs everything from scratch following the official guide.

---

## ⚡ Quick Commands

```bash
# Activate environment
conda activate cosyvoice
# or
source activate_env.sh

# Start service
./start_service.sh

# Stop service
./stop_service.sh

# View logs
tail -f tts_service.log

# Check status
ps aux | grep tts_server
```

---

## 🐛 Common Issues

### "Conda command not found"

**Fix:**
```bash
# Install Conda first
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
exec bash
```

### "CosyVoice import fails"

**Fix:**
```bash
# Re-run setup
./setup.sh

# Verify
conda activate cosyvoice
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('OK')"
```

### "Model download fails"

**Fix:**
```bash
# Pre-download manually
conda activate cosyvoice
cd CosyVoice
python -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')"
```

### "Service won't start"

**Fix:**
```bash
# Check logs for errors
cat tts_service.log

# Run in foreground to see errors
conda activate cosyvoice
python tts_server.py
```

---

## 💡 Key Differences

| Aspect | Old (Broken) | New (Official) |
|--------|--------------|----------------|
| Environment | Python venv | **Conda** |
| Python | 3.9+ | **3.8** (required) |
| CosyVoice | Copied files | **Official clone** |
| Dependencies | Custom | **Official requirements.txt** |
| Imports | PYTHONPATH hacks | **sitecustomize.py** |
| Model API | Custom code | **Official inference_sft** |

---

## 🎓 Understanding the Setup

### Why Conda?

CosyVoice officially requires Conda for dependency management. Using venv caused compatibility issues.

### Why Python 3.8?

CosyVoice is tested and optimized for Python 3.8. Other versions may have issues.

### Why Clone Repository?

The official repository includes:
- Correct directory structure
- Third-party dependencies (Matcha-TTS)
- Official model loading code
- Testing utilities

### Why Official Requirements?

The official requirements.txt includes:
- Correct versions of all dependencies
- Special packages (WeTextProcessing, etc.)
- Compatibility-tested combinations

---

## 🚀 Next Steps

1. **Setup:** Run `./setup.sh` (if not done)
2. **Start:** Run `./start_service.sh`
3. **Test:** Try the verification commands above
4. **Integrate:** Use the API in your voice agent

---

## 📞 Getting Help

### Service Issues
1. Check logs: `tail -f tts_service.log`
2. Run in foreground: `python tts_server.py`
3. Check [SERVER_SETUP_GUIDE.md](SERVER_SETUP_GUIDE.md) troubleshooting section

### CosyVoice Issues
1. Check official repo: https://github.com/FunAudioLLM/CosyVoice
2. Read their documentation
3. Check their GitHub issues

### Installation Issues
1. Read [INSTALLATION.md](INSTALLATION.md)
2. Verify all prerequisites
3. Check system requirements

---

## ✅ Success Checklist

After setup, you should have:

- [x] Conda installed and working
- [x] `cosyvoice` conda environment created
- [x] CosyVoice repository cloned
- [x] All dependencies installed
- [x] Python imports working
- [x] Model downloaded
- [x] Service starts successfully
- [x] API responds to requests

If all checked, you're ready to use the service! 🎉

---

## 📊 What You Get

### Supported Languages
- Chinese (Mandarin)
- English
- Japanese
- Korean
- Cantonese

### Available Speakers
- 中文女 (Chinese Female)
- 中文男 (Chinese Male)
- 英文女 (English Female)
- 英文男 (English Male)
- 日语男 (Japanese Male)
- 韩语女 (Korean Female)
- 粤语女 (Cantonese Female)

### Features
- Real-time streaming
- HTTP REST API
- WebSocket support
- Multiple audio formats
- Configurable voice parameters
- Low latency optimization

---

## 🔗 Official Resources

- **CosyVoice GitHub:** https://github.com/FunAudioLLM/CosyVoice
- **ModelScope Models:** https://www.modelscope.cn/models/iic
- **Paper:** https://arxiv.org/abs/2407.05407

---

**Ready to start?** Run `./setup.sh` now! 🚀

For detailed server deployment instructions, see **[SERVER_SETUP_GUIDE.md](SERVER_SETUP_GUIDE.md)**.

