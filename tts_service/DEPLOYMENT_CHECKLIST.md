# Deployment Checklist - Model Download Fix

## 📋 Pre-Deployment Verification

### Local Changes Complete ✅
- [x] `synthesis.py` - Model verification and auto-repair logic
- [x] `config.py` - Configuration flags for verification/repair
- [x] `download_model.py` - Standalone model management tool
- [x] `start_service.sh` - Pre-flight model checks
- [x] `tts_manager.sh` - Added verify/repair commands
- [x] Documentation files (for later)

### Code Quality ✅
- [x] No syntax errors
- [x] Import warnings only (expected - packages in conda env)
- [x] Backward compatible
- [x] Configuration defaults enable auto-repair
- [x] Error handling comprehensive

---

## 🚀 Deployment to RunPod

### Option 1: Git Push (Recommended)

**On local machine:**
```bash
cd /Users/deku/Desktop/Code/PurpleCodebase/AI-Development/voice-agent-server-setup

# Stage changes
git add tts_service/synthesis.py
git add tts_service/config.py
git add tts_service/download_model.py
git add tts_service/start_service.sh
git add tts_service/tts_manager.sh

# Commit
git commit -m "fix: Add automatic model verification and repair

- Add file integrity verification before model loading
- Auto-detect and repair incomplete model downloads  
- Add standalone download_model.py tool
- Enhance start_service.sh with pre-flight checks
- Add verify/repair commands to tts_manager.sh
- Fix missing speech_tokenizer_v1.onnx issue

Resolves incomplete model download issue on RunPod"

# Push
git push origin feat/shell-setup-v2.0.0
```

**On RunPod instance:**
```bash
cd /workspace/apps/voice-agent-server-setup

# Pull changes
git pull origin feat/shell-setup-v2.0.0

# Make scripts executable
chmod +x tts_service/download_model.py
chmod +x tts_service/start_service.sh
chmod +x tts_service/tts_manager.sh

# Stop service
cd tts_service
./stop_service.sh

# Restart (will auto-fix)
./start_service.sh

# Monitor logs
tail -f tts_service.log
```

### Option 2: Manual File Copy

**If git is not available:**

```bash
# On local machine
cd /Users/deku/Desktop/Code/PurpleCodebase/AI-Development/voice-agent-server-setup/tts_service

# Copy files to RunPod (adjust connection details)
scp synthesis.py root@RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/
scp config.py root@RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/
scp download_model.py root@RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/
scp start_service.sh root@RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/
scp tts_manager.sh root@RUNPOD_IP:/workspace/apps/voice-agent-server-setup/tts_service/

# On RunPod instance
cd /workspace/apps/voice-agent-server-setup/tts_service
chmod +x download_model.py start_service.sh tts_manager.sh
./stop_service.sh
./start_service.sh
```

### Option 3: Quick Fix Without Code Update

**If you just want to fix the immediate issue:**

```bash
# On RunPod instance
cd /workspace/apps/voice-agent-server-setup/tts_service

# Remove incomplete model
rm -rf pretrained_models/CosyVoice-300M-SFT

# Restart (will download fresh)
./stop_service.sh
./start_service.sh
```

---

## ✅ Post-Deployment Verification

### 1. Check Service Started
```bash
# Should see PID and success message
ps aux | grep tts_server.py
```

### 2. Check Logs
```bash
tail -50 tts_service.log

# Look for:
# ✓ Model directory found
# Verifying model file integrity...
# ✓ All required model files present
# ✓ Model loaded successfully
```

### 3. Test Health Endpoint
```bash
curl http://localhost:8002/health

# Expected:
# {
#   "status": "healthy",
#   "model": "CosyVoice-300M-SFT",
#   "device": "cuda"
# }
```

### 4. Test Synthesis
```bash
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing model fix"}' \
  --output test.wav

# Check file created
ls -lh test.wav
# Should be > 0 bytes
```

### 5. Verify Model Files
```bash
# Using new tool
python download_model.py --verify-only

# Or manually
ls -lh pretrained_models/CosyVoice-300M-SFT/speech_tokenizer_v1.onnx
# Should show ~89MB file
```

---

## 📊 Expected Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Deploy code | 2 min | Manual |
| Stop service | 5 sec | Auto |
| Detect incomplete model | 5 sec | Auto |
| Download complete model | 2-5 min | Auto |
| Verify files | 5 sec | Auto |
| Load model | 30-60 sec | Auto |
| **Total** | **3-8 min** | |

---

## 🎯 Success Criteria

- [ ] Service starts without falling back to basic TTS
- [ ] All 6 required model files present
- [ ] Health endpoint returns "healthy"
- [ ] Synthesis produces valid audio files
- [ ] Logs show "Model loaded successfully"
- [ ] No errors in logs

---

## 🚨 Rollback Plan

If issues occur after deployment:

### Quick Rollback
```bash
# On RunPod
cd /workspace/apps/voice-agent-server-setup

# Revert code
git reset --hard HEAD~1

# Restart service
cd tts_service
./stop_service.sh
./start_service.sh
```

### Alternative: Keep code, disable auto-repair
```python
# Edit config.py on RunPod
ServiceConfig(
    verify_model_integrity=False,  # Disable checks
    auto_repair_model=False,       # Disable auto-repair
)
```

---

## 📝 Documentation Updates (Later)

**Note:** Per user request, documentation will be updated in a separate task.

Files to update later:
- [ ] README.md - Add troubleshooting section
- [ ] QUICKSTART.md - Update model download info  
- [ ] CLIENT_API_GUIDE.md - No changes needed
- [ ] CONFIG_REFERENCE.md - Document new config fields

---

## 🔍 Monitoring

### During Deployment
```bash
# Watch logs in real-time
tail -f tts_service.log

# Check for errors
grep ERROR tts_service.log

# Check model download progress
grep "Downloading model" tts_service.log -A 20
```

### Post-Deployment
```bash
# Service status
./tts_manager.sh status

# Model verification
./tts_manager.sh verify

# Service logs
./tts_manager.sh logs
```

---

## 🎓 What Changed (For Reference)

### Behavior Changes:
1. **Before:** Directory exists → Assume complete → Load fails → Fallback
2. **After:** Directory exists → Verify files → Auto-repair if needed → Load succeeds

### New Capabilities:
- Automatic incomplete model detection
- Automatic model repair (re-download)
- Standalone verification tool
- Manual repair commands
- Configurable verification/repair

### No Breaking Changes:
- Default behavior: Auto-repair enabled
- Existing deployments benefit immediately
- Can opt-out via config if needed
- All existing APIs unchanged

---

## ✨ Summary

**What to do:**
1. Push/copy code to RunPod
2. Restart service
3. Wait 3-8 minutes (first time)
4. Verify service is healthy

**What happens automatically:**
1. Service detects incomplete model
2. Removes old incomplete files
3. Downloads complete model
4. Verifies all files present
5. Loads successfully

**No manual intervention required!** 🎉

---

## 📞 Support

If issues persist after deployment:

1. Check logs: `tail -100 tts_service.log`
2. Verify model: `./tts_manager.sh verify`
3. Try repair: `./tts_manager.sh repair`
4. Full reset: Remove model dir and restart

**Status: READY FOR DEPLOYMENT** ✅

