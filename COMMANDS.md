# 🎙️ Voice Agent Server - Complete Command Reference

---

## 🧭 Command Flow

**Setup → Configure → Test Models → Start → Monitor → Use → Stop**

↓   ↓   ↓   ↓   ↓

**Individual → Debug Mode → Restart → Test → Maintain**

---

## 🚀 First-Time Setup

### `./setup.sh`

- Complete installation: system deps + Python deps (Poetry) + venv + directory structure
- **Time:** 15–20 minutes
- **Runs:**
    - `scripts/install/install-system-deps.sh`
    - Poetry to resolve and install Python dependencies

### `scripts/install/install-system-deps.sh`

- Installs system packages (Python 3.11, ffmpeg, git, etc.)
- **Use when:** Reinstalling system dependencies only

### Python Dependencies (Poetry)

- Managed via `pyproject.toml` with pinned versions (PyTorch CUDA via extra index)
- **Update deps:**
  ```bash
  source venv/bin/activate
  poetry update
  ```

---

## ⚙️ Configuration

```bash
nano config/stt.env
nano config/tts.env
nano config/llm.env

```

Edit API keys and service-specific settings

```bash
nano config/system.env
```

Edit system-wide settings (CUDA, paths, environment variables)

```bash
nano config/ports.conf
```

Change service ports if needed (default: 8000, 8001, 8002)

---

## 🧪 Test Model Loading (Debug Mode)

```bash
source venv/bin/activate
python scripts/debug/test-stt-model.py
python scripts/debug/test-tts-model.py
python scripts/debug/test-llm-model.py
deactivate
```

Test models without starting full services.

**Time:** STT ~25s | TTS ~28s | LLM ~75s

Alternative:

```bash
python services/stt_service/load_model.py
python services/tts_service/load_model.py
python services/llm_service/load_model.py
```

---

## ▶️ Start Services

```bash
./bin/start-all.sh
```

Start all services (STT:8000, TTS:8001, LLM:8002)

**Time:** 2–3 minutes

**Individual:**

```bash
./bin/start-stt.sh
./bin/start-tts.sh
./bin/start-llm.sh
```

Internal starters (don’t call directly):

```
services/stt_service/start.sh
services/tts_service/start.sh
services/llm_service/start.sh
```

---

## ⏹️ Stop Services

```bash
./bin/stop-all.sh
```

Stop all services gracefully

**Individual:**

```bash
./bin/stop-stt.sh
./bin/stop-tts.sh
./bin/stop-llm.sh
```

Internal stoppers (don’t call directly):

```
services/stt_service/stop.sh
services/tts_service/stop.sh
services/llm_service/stop.sh
```

---

## 🔄 Restart Services

```bash
./bin/restart-all.sh
```

Restart all services (stop + start)

**Individual:**

```bash
./bin/restart-stt.sh
./bin/restart-tts.sh
./bin/restart-llm.sh
```

Use after updating corresponding service files (`stt_main.py`, `tts_main.py`, `llm_main.py`)

---

## 📊 Monitoring & Status

```bash
./bin/status-all.sh
```

Quick status (running/stopped, PIDs, ports)

```bash
./bin/health-check.sh
```

Comprehensive health (GPU, CPU, RAM, endpoints)

**Exit codes:**

0 → Healthy 1 → Partial 2 → Down

```bash
./bin/monitor.sh
```

Real-time dashboard (GPU stats, logs)

Exit: `Ctrl+C`

---

## 📝 View Logs

**Live tail:**

```bash
tail -f logs/stt/stt_*.log
tail -f logs/tts/tts_*.log
tail -f logs/llm/llm_*.log
```

**Last 100 lines:**

```bash
tail -n 100 logs/stt/stt_*.log
tail -n 100 logs/tts/tts_*.log
tail -n 100 logs/llm/llm_*.log
```

**Search logs:**

```bash
grep -r "ERROR" logs/
grep -r "✗" logs/
grep "Transcription" logs/stt/*.log | tail -20
```

---

## 🖥️ GPU Monitoring

```bash
./scripts/utils/check-gpu.sh
nvidia-smi
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
watch -n 1 nvidia-smi
```

Use for GPU info, utilization, and live monitoring.

---

## 🧪 Integration Testing

```bash
./tests/integration/test-stt-api.sh
./tests/integration/test-tts-api.sh
./tests/integration/test-llm-api.sh
```

Validate APIs, health, and auth.

---

## ⚡ Performance Testing

```bash
./tests/performance/benchmark-all.sh
./tests/performance/benchmark-stt.sh
./tests/performance/benchmark-tts.sh
./tests/performance/benchmark-llm.sh
```

Benchmark latency, throughput, VRAM usage.

**Time:** ~3–5 min

---

## 💪 Stress Testing

```bash
./tests/load/stress-test-stt.py
./tests/load/stress-test-tts.py
./tests/load/stress-test-llm.py
```

Test services under concurrent requests.

---

## 🔧 Manual API Testing

```bash
curl -X POST "http://localhost:8000/health"
curl -X POST "http://localhost:8001/health"
curl -X POST "http://localhost:8002/health"

curl -X POST "http://localhost:8000/transcribe?language=hi" -H "Authorization: Bearer YOUR_KEY" -F "file=@audio.wav"
curl -X POST "http://localhost:8001/synthesize?text=hello&language=en" -H "Authorization: Bearer YOUR_KEY" -o output.wav
curl -X POST "http://localhost:8002/v1/chat/completions" -H "Authorization: Bearer YOUR_KEY" -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"test"}]}'
```

---

## 🛠️ Utilities

```bash
./scripts/utils/cleanup-logs.sh
./scripts/utils/backup-config.sh
./scripts/utils/optimize-cuda.sh
./scripts/utils/cleanup-setup.sh
```

- Cleanup logs
- Backup config
- Optimize CUDA performance
- Cleanup old setup artifacts (venv, CosyVoice clone, .pth, pip cache)

---

## 📂 Direct File Editing

```bash
nano services/stt_service/app/stt_main.py
nano services/tts_service/app/tts_main.py
nano services/llm_service/app/llm_main.py
```

Restart respective service after editing.

---

## 📋 Common Workflows

### **Daily Startup**

```bash
./bin/start-all.sh
./bin/status-all.sh
./bin/monitor.sh  # optional
```

### **After Code Changes**

```bash
nano services/stt_service/app/stt_main.py
./bin/restart-stt.sh
tail -f logs/stt/stt_*.log
curl http://localhost:8000/health
```

### **Service Won’t Start**

```bash
./bin/stop-stt.sh
source venv/bin/activate
python scripts/debug/test-stt-model.py
deactivate
tail -n 50 logs/stt/stt_*.log | grep ERROR
./bin/start-stt.sh
```

### **Full System Test**

```bash
./bin/start-all.sh
./bin/health-check.sh
./tests/integration/test-stt-api.sh
./tests/integration/test-tts-api.sh
./tests/integration/test-llm-api.sh
./tests/performance/benchmark-all.sh
```

### **Performance Analysis**

```bash
./bin/health-check.sh
./tests/performance/benchmark-all.sh
watch -n 1 nvidia-smi
```

### **End of Day**

```bash
./bin/stop-all.sh
./scripts/utils/cleanup-logs.sh  # optional weekly
```

### **Weekly Maintenance**

```bash
./scripts/utils/backup-config.sh
./scripts/utils/cleanup-logs.sh
./bin/health-check.sh
./tests/performance/benchmark-all.sh

```

---

## 🎯 Quick Reference

**Service Ports**

| Service | Port |
| --- | --- |
| STT | 8000 |
| TTS | 8001 |
| LLM | 8002 |

**Important Paths**

| Type | Path |
| --- | --- |
| Configs | `config/*.env` |
| Logs | `logs/stt/`, `logs/tts/`, `logs/llm/` |
| PIDs | `pids/*.pid` |
| Python | `services/*/app/*.py` |
| Tests | `tests/integration/`, `tests/performance/`, `tests/load/` |

**Exit Codes**

| Code | Meaning |
| --- | --- |
| 0 | Success / All healthy |
| 1 | Partial failure / Some services down |
| 2 | Total failure / All services down |