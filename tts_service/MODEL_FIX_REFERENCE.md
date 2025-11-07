# Model Fix - Quick Reference Card

## 🎯 Problem
Service falls back to basic TTS mode due to incomplete model (missing `speech_tokenizer_v1.onnx`)

## ✅ Solution
Automatic detection and repair - **just restart the service!**

---

## Quick Commands

### On RunPod Instance:

```bash
# 1. Stop service
./stop_service.sh

# 2. Restart (auto-detects and repairs)
./start_service.sh

# 3. Watch logs
tail -f tts_service.log
```

**That's it!** The service will automatically:
- Detect incomplete model
- Remove old files  
- Download complete model (~1GB, ~2-5 mins)
- Verify all files present
- Start successfully

---

## Manual Commands (If Needed)

### Verify Model Integrity
```bash
./tts_manager.sh verify
# or
python download_model.py --verify-only
```

### Force Repair
```bash
./tts_manager.sh repair
# or
python download_model.py --force
```

### Complete Reset
```bash
rm -rf pretrained_models/CosyVoice-300M-SFT
./start_service.sh
```

---

## Success Indicators

### ✅ Working (Look for in logs):
```
✓ Model directory found
Verifying model file integrity...
✓ All required model files present
✓ Model loaded successfully
```

### ✅ Auto-Repair in Progress:
```
✗ Model is INCOMPLETE! Missing files: ['speech_tokenizer_v1.onnx']
Auto-repair enabled. Attempting to re-download complete model...
Downloading model: iic/CosyVoice-300M-SFT
...
✓ All required files present
✓ Model loaded successfully
```

### ❌ Problem (Old behavior):
```
✗ Model initialization failed: speech_tokenizer_v1.onnx doesn't exist
ENTERING FALLBACK MODE
```

---

## Configuration (config.py)

```python
ServiceConfig(
    verify_model_integrity=True,   # Check files before loading
    auto_repair_model=True,        # Auto-fix if incomplete
    use_modelscope=True,           # Enable auto-download
)
```

---

## Required Files

Model is **complete** when all these exist:
- ✅ `speech_tokenizer_v1.onnx` (89 MB) ⭐ Most important
- ✅ `campplus.onnx` (27 MB)
- ✅ `flow.decoder.estimator.fp32.onnx` (314 MB)
- ✅ `cosyvoice.yaml` (6 KB)
- ✅ `flow.pt` (401 MB)
- ✅ `hift.pt` (38 MB)

**Total: ~870 MB**

---

## Timeline

| Action | Time |
|--------|------|
| Stop service | 5 sec |
| Detect incomplete | 5 sec |
| Download model | 2-5 min |
| Verify files | 5 sec |
| Load model | 30-60 sec |
| **Total** | **3-7 min** |

*Subsequent starts: 30-60 sec (model already complete)*

---

## Troubleshooting

### Download Fails
```bash
# Check connectivity
curl -I https://modelscope.cn

# Try again
python download_model.py --force
```

### Still in Fallback Mode
```bash
# Check actual error
tail -50 tts_service.log

# Verify conda env
conda activate cosyvoice
python -c "from cosyvoice.cli.cosyvoice import CosyVoice"
```

### Disk Space
```bash
df -h /workspace
# Need at least 2GB free
```

---

## Files Changed (Code)

1. **synthesis.py** - Added verification & auto-repair
2. **config.py** - Added config flags  
3. **download_model.py** - New standalone tool
4. **start_service.sh** - Added pre-flight check
5. **tts_manager.sh** - Added verify/repair commands

---

## Health Check

```bash
# After service starts
curl http://localhost:8002/health

# Should show:
{
  "status": "healthy",
  "model": "CosyVoice-300M-SFT",
  "device": "cuda"
}
```

---

## Summary

✅ **Automatic fix** - just restart
✅ **Manual tools** - `verify` and `repair` commands
✅ **Better logging** - see what's happening
✅ **Configurable** - can disable if needed
✅ **No breaking changes** - backward compatible

**Just restart the service and it will auto-fix!** 🎉

