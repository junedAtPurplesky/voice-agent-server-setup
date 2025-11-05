# LLM Service Testing - Quick Reference Card

## 🚀 Getting Started (Choose One)

### Option 1: Instant Testing (Recommended)
```bash
python3 test_client.py
```
**First run**: Auto-creates venv, installs deps (~30s)  
**After**: Instant, uses existing environment

### Option 2: Shell Tests (No Setup)
```bash
./test_llm.sh quick
```
**Always instant**, requires only: curl, jq, bc

---

## 📋 Common Commands

### Quick Tests
| Command | What It Does | Time |
|---------|-------------|------|
| `./test_llm.sh quick` | Shell-based smoke test | 10s |
| `python3 test_client.py` | Comprehensive test | 30s |
| `./run_test.sh quick` | Same as above | 30s |

### Streaming Tests
| Command | What It Does |
|---------|-------------|
| `python3 test_stream.py` | Test streaming (5 prompts) |
| `python3 test_stream.py --verbose` | Show real-time output |
| `python3 test_stream.py --num-tests 20` | More comprehensive |

### Load Tests
| Command | What It Does |
|---------|-------------|
| `python3 load_test.py` | Default: 100 req, 10 concurrent |
| `python3 load_test.py --requests 500 --concurrent 25` | Heavy load |
| `python3 load_test.py --stream` | Test streaming under load |

### Individual Endpoint Tests
| Command | Endpoint |
|---------|----------|
| `./test_llm.sh health` | Health check |
| `./test_llm.sh completion` | Completion |
| `./test_llm.sh chat` | Chat |
| `./test_llm.sh stream` | Streaming |

---

## 🎯 Smart Runner Shortcuts

```bash
./run_test.sh quick       # Run test_client.py
./run_test.sh stream      # Run test_stream.py
./run_test.sh load        # Run load_test.py
./run_test.sh examples    # Run example_usage.py
```

**With parameters:**
```bash
./run_test.sh test_client.py --requests 100
./run_test.sh load_test.py --requests 1000 --concurrent 50
```

---

## 📊 What You Get

### test_client.py
✅ Success rate  
✅ Response times (min/max/mean/median/stdev)  
✅ Token statistics and throughput  
✅ Tests all endpoints (completion, chat, streaming)

### test_stream.py
✅ Time to first token  
✅ Chunk timing (min/max/avg)  
✅ Streaming throughput  
✅ Real-time output (with --verbose)

### load_test.py
✅ P50, P95, P99 latencies  
✅ Requests per second  
✅ Error breakdown  
✅ Status code distribution  
✅ Ramp-up support

---

## 🔧 Testing Different Services

### Local
```bash
python3 test_client.py
# Uses http://127.0.0.1:8000 by default
```

### Remote
```bash
python3 test_client.py --url http://192.168.1.100:8000
```

### Different Port
```bash
python3 test_client.py --url http://127.0.0.1:8080
```

---

## 📖 Documentation

| File | What It's For |
|------|--------------|
| `QUICKSTART_TESTING.md` | **Start here** (2 min) |
| `TESTING.md` | Complete guide (detailed) |
| `TEST_EXAMPLES.md` | Copy-paste examples |
| `AUTO_SETUP.md` | How auto-venv works |

---

## 🛠️ Common Scenarios

### After Making Changes
```bash
./test_llm.sh quick
```

### Before Deploying
```bash
python3 test_client.py --requests 50
python3 test_stream.py --num-tests 10
python3 load_test.py --requests 200 --concurrent 20
```

### Finding Capacity
```bash
# Gradually increase concurrent requests
python3 load_test.py --requests 50 --concurrent 5
python3 load_test.py --requests 50 --concurrent 10
python3 load_test.py --requests 50 --concurrent 20
```

### Monitoring Performance
```bash
# Run periodically
python3 load_test.py --requests 100 --concurrent 10 > metrics.txt
```

---

## ⚠️ Troubleshooting

### Service Not Running
```bash
./llm_manager.sh status    # Check status
./llm_manager.sh start     # Start service
./llm_manager.sh logs      # View logs
```

### Tests Timing Out
```bash
# Increase timeout
python3 load_test.py --timeout 300

# Reduce concurrent requests
python3 test_client.py --requests 10 --concurrent 2
```

### Recreate Test Environment
```bash
rm -rf .test_venv
python3 test_client.py  # Will recreate automatically
```

---

## 💡 Pro Tips

1. **Start small**: Begin with `./test_llm.sh quick`
2. **Monitor logs**: Run `./llm_manager.sh logs` in another terminal
3. **Use ramp-up**: For realistic load: `--ramp-up 10`
4. **Check P95/P99**: More important than average latency
5. **Test streaming separately**: Different performance characteristics

---

## 🎓 Examples

### Custom Test Script
```python
from test_client import LLMTestClient

async def my_test():
    client = LLMTestClient()
    result = await client.test_completion(prompt="Test")
    print(f"Response time: {result.response_time}s")
```

### Batch Testing
```bash
for i in {1..5}; do
  echo "Run $i:"
  python3 test_client.py --requests 20
  sleep 30
done
```

### CI/CD
```bash
#!/bin/bash
python3 test_client.py --requests 20 || exit 1
python3 load_test.py --requests 50 || exit 1
```

---

## 📱 One-Liners

```bash
# Health check
curl http://127.0.0.1:8000/v1/models | jq

# Quick test
./test_llm.sh quick

# Full test suite
python3 test_client.py && python3 test_stream.py && python3 load_test.py

# Find max concurrent
for c in 5 10 20 50; do python3 load_test.py --requests 50 --concurrent $c; done

# Monitor continuously
watch -n 300 'python3 load_test.py --requests 50 --concurrent 10'
```

---

## ✨ Remember

**Zero setup required!** Just run:
```bash
python3 test_client.py
```

First run creates environment automatically. Future runs are instant!

---

## 📞 Quick Help

```bash
python3 test_client.py --help
python3 test_stream.py --help
python3 load_test.py --help
./test_llm.sh help
```

---

**That's it! You're ready to test your LLM service! 🎉**

