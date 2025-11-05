# CosyVoice TTS Service - Quick Reference Card

## 🚀 Installation (First Time)

**✨ NEW:** Conda auto-installs if not present!

```bash
# 1. Run setup (handles everything automatically)
cd tts_service
./setup.sh

# 2. Start service
./start_service.sh
```

**Note:** If Conda is not installed, setup.sh will automatically:
- Download and install Miniconda
- Support Linux (x86_64/ARM64) and macOS (Intel/Apple Silicon)
- Initialize it for your shell

---

## 🎮 Daily Commands

```bash
# Start service
./start_service.sh

# Stop service
./stop_service.sh

# Restart service
./stop_service.sh && ./start_service.sh

# View logs
tail -f tts_service.log

# Check status
./tts_manager.sh status

# Activate environment
conda activate cosyvoice
```

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8002/health

# List voices
curl http://localhost:8002/voices

# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

# Run test suite
conda activate cosyvoice
python test_client.py
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `setup.sh` | Install everything |
| `start_service.sh` | Start the service |
| `stop_service.sh` | Stop the service |
| `activate_env.sh` | Activate conda env |
| `config.py` | Service configuration |
| `tts_service.log` | Service logs |

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `START_HERE.md` | **Read this first!** |
| `SERVER_SETUP_GUIDE.md` | Server deployment |
| `INSTALLATION.md` | Detailed install steps |
| `CLIENT_API_GUIDE.md` | API usage examples |
| `REFACTOR_SUMMARY.md` | What changed |

---

## 🔧 Troubleshooting

### Service won't start
```bash
cat tts_service.log
conda activate cosyvoice
python tts_server.py  # Run in foreground
```

### Import errors
```bash
./setup.sh  # Re-run setup
```

### Model not found
```bash
conda activate cosyvoice
cd CosyVoice
python -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')"
```

---

## ⚙️ Configuration

Edit `config.py`:

```python
class ServiceConfig(BaseModel):
    model_name: str = "CosyVoice-300M-SFT"
    model_path: str = "pretrained_models/CosyVoice-300M-SFT"
    host: str = "0.0.0.0"
    port: int = 8002  # Change port here
    log_level: str = "info"  # or "debug"
```

---

## 🌐 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/voices` | GET | List voices |
| `/config/defaults` | GET | Get config |
| `/synthesize` | POST | Synthesize text |
| `/synthesize/stream` | POST | Stream synthesis |
| `/stream` | WebSocket | Real-time streaming |

---

## 🎤 Available Voices

- `中文女` (Chinese Female)
- `中文男` (Chinese Male)
- `英文女` (English Female)
- `英文男` (English Male)
- `日语男` (Japanese Male)
- `韩语女` (Korean Female)
- `粤语女` (Cantonese Female)

---

## 📊 System Requirements

**Minimum:**
- Conda installed
- Python 3.8
- 8 GB RAM
- 10 GB disk space

**Recommended:**
- NVIDIA GPU (4GB+ VRAM)
- 16 GB+ RAM
- 20 GB+ disk space
- CUDA 11.8+

---

## 🔗 Quick Links

- **Official CosyVoice:** https://github.com/FunAudioLLM/CosyVoice
- **ModelScope:** https://www.modelscope.cn/models/iic
- **Paper:** https://arxiv.org/abs/2407.05407

---

## ✅ Health Check

After setup, verify:

```bash
# 1. Environment exists
conda env list | grep cosyvoice

# 2. Python version correct
conda activate cosyvoice && python --version

# 3. CosyVoice imports
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('OK')"

# 4. Service responds
curl http://localhost:8002/health

# 5. Synthesis works
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

All should pass! ✅

---

**Need more details?** Read [START_HERE.md](START_HERE.md) or [SERVER_SETUP_GUIDE.md](SERVER_SETUP_GUIDE.md)

