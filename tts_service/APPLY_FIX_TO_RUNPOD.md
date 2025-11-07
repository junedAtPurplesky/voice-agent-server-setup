# Apply Model Download Fix to RunPod Instance

## 🎯 Quick Summary

Your RunPod instance has an incomplete model (missing `speech_tokenizer_v1.onnx`). 

The updated code will **automatically detect and fix** this issue.

---

## 📦 Files Changed

1. **`synthesis.py`** - Added automatic model verification and repair
2. **`download_model.py`** - New standalone tool for model management (NEW FILE)
3. **`QUICKSTART.md`** - Added troubleshooting section
4. **`MODEL_DOWNLOAD_FIX.md`** - Comprehensive documentation (NEW FILE)

---

## 🚀 Apply Fix (3 Methods)

### Method 1: Git Pull (Recommended)

If your RunPod instance has git access to this repo:

```bash
# On RunPod instance
cd /workspace/apps/voice-agent-server-setup/tts_service

# Pull latest changes
git pull origin feat/shell-setup-v2.0.0

# Stop service
./stop_service.sh

# Restart - will auto-fix the model
./start_service.sh

# Watch it work
tail -f tts_service.log
```

### Method 2: Manual File Copy

If you need to manually copy files:

```bash
# On your local machine (from this repo)
cd /Users/deku/Desktop/Code/PurpleCodebase/AI-Development/voice-agent-server-setup/tts_service

# Copy to RunPod using scp or your preferred method
# (Replace with your RunPod details)
scp synthesis.py root@YOUR_RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/
scp download_model.py root@YOUR_RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/

# Then on RunPod instance
chmod +x /workspace/apps/voice-agent-server-setup/tts_service/download_model.py
./stop_service.sh
./start_service.sh
```

### Method 3: Manual Download & Restart (No Code Update)

If you just want to fix the current issue without updating code:

```bash
# On RunPod instance
cd /workspace/apps/voice-agent-server-setup/tts_service

# Stop service
./stop_service.sh

# Remove incomplete model
rm -rf pretrained_models/CosyVoice-300M-SFT

# Start service - will auto-download complete model
./start_service.sh

# Watch download progress
tail -f tts_service.log
```

---

## ✅ Verify Fix Applied

After restarting, check logs for these indicators:

### ✅ Success Messages

```
======================================================================
CHECKING MODEL AVAILABILITY AND INTEGRITY
======================================================================
Looking for model at: /workspace/.../CosyVoice-300M-SFT
✓ Model directory found
Verifying model file integrity...
✗ Model is INCOMPLETE! Missing files: ['speech_tokenizer_v1.onnx']

Attempting to re-download complete model...
Downloading model: iic/CosyVoice-300M-SFT
...
✓ Model downloaded to: ...
✓ All required files present

======================================================================
INITIALIZING COSYVOICE MODEL
======================================================================
✓ Model loaded successfully
```

### ❌ Old Behavior (Before Fix)

```
✓ Model found at: ...
(tries to load)
✗ Model initialization failed: speech_tokenizer_v1.onnx doesn't exist
ENTERING FALLBACK MODE
```

---

## 🧪 Test After Fix

Once service is running:

```bash
# Health check
curl http://localhost:8002/health

# Should return
{
  "status": "healthy",
  "model": "CosyVoice-300M-SFT",
  "device": "cuda"
}

# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world, this is a test"}' \
  --output test.wav

# Check file was created
ls -lh test.wav
```

---

## 📊 Expected Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Stop service | 5 seconds | |
| Apply code changes | 1 minute | If using git pull |
| Start service | 30 seconds | Just startup |
| Detect incomplete model | 5 seconds | New verification |
| Download complete model | 2-5 minutes | ~870 MB download |
| Initialize model | 30-60 seconds | Load into memory |
| **Total** | **4-7 minutes** | First time after fix |
| **Subsequent starts** | **30-60 seconds** | Model already complete |

---

## 🔍 Troubleshooting

### If download fails

```bash
# Check internet connection
curl -I https://modelscope.cn

# Try manual download
python download_model.py --force
```

### If service still uses fallback mode

```bash
# Check logs for actual error
tail -50 tts_service.log

# Verify conda environment
conda activate cosyvoice
python -c "from cosyvoice.cli.cosyvoice import CosyVoice; print('OK')"
```

### If disk space issues

```bash
# Check space
df -h /workspace

# Clean old models if needed
rm -rf pretrained_models/CosyVoice-300M-SFT.old
```

---

## 🎓 What Changed Technically

### Before
```python
# Old code just checked if directory exists
if not os.path.exists(model_path):
    download_model()
else:
    # Assumes model is complete! ❌
    load_model()
```

### After
```python
# New code verifies all files
if not os.path.exists(model_path):
    download_model()
else:
    # Verify integrity
    is_complete, missing = verify_model_files()
    if not is_complete:
        # Auto-fix! ✅
        re_download_model()
    load_model()
```

---

## 📝 Quick Commands Reference

```bash
# Stop service
./stop_service.sh

# Start service (will auto-fix)
./start_service.sh

# Watch logs in real-time
tail -f tts_service.log

# Verify model manually
python download_model.py --verify-only

# Force re-download
python download_model.py --force

# Check service status
curl http://localhost:8002/health

# View service info
./tts_manager.sh status
```

---

## ✨ Benefits After Fix

- ✅ **Automatic detection** of incomplete models
- ✅ **Automatic repair** without manual intervention  
- ✅ **Detailed logging** so you know what's happening
- ✅ **Standalone tools** for manual verification if needed
- ✅ **Prevention** of future incomplete downloads

---

## 🎉 That's It!

After applying the fix and restarting, your service should:

1. Detect the incomplete model automatically
2. Remove the incomplete files
3. Download the complete model (~870 MB)
4. Verify all files are present
5. Load successfully and be ready to serve requests

**No manual commands needed** - just restart the service!

---

**Need help?** Check `MODEL_DOWNLOAD_FIX.md` for detailed technical information.

