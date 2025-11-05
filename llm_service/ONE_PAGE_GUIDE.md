# One-Page Testing Guide

## 🚀 Complete Testing in 5 Steps (10 Minutes)

### Step 1: Start Service (2 min)
```bash
cd llm_service
./llm_manager.sh start
./llm_manager.sh status  # Verify it's running
```

### Step 2: Quick Verification (2 min)
```bash
./test_llm.sh quick
```
✅ Expect: All tests passed

### Step 3: Comprehensive Test (2 min)
```bash
python3 test_client.py
```
✅ Expect: Success rate 100%, all tests passed

### Step 4: Streaming Test (2 min)
```bash
python3 test_stream.py
```
✅ Expect: 5/5 streams successful

### Step 5: Load Test (2 min)
```bash
python3 load_test.py --requests 50 --concurrent 5
```
✅ Expect: Success rate >95%

## ✅ Done!

Your service is tested and ready!

### What You Tested:
- ✅ Health endpoint
- ✅ Text completions
- ✅ Chat completions
- ✅ Streaming
- ✅ Concurrent requests
- ✅ Load capacity
- ✅ Resource usage (GPU/RAM/CPU)

### Results You Should See:
- Success rate: >95%
- Response time: <3s
- No timeouts
- Stable resources

## 🐛 Quick Troubleshooting

### Service not running?
```bash
./llm_manager.sh logs
```

### Tests failing?
```bash
curl http://127.0.0.1:8000/v1/models
```

### Need more details?
```bash
# See complete guide
cat COMPLETE_TESTING_STEPS.md

# See examples
cat TEST_EXAMPLES.md
```

## 📊 All Test Commands

```bash
# Shell tests (no setup)
./test_llm.sh quick
./test_llm.sh health
./test_llm.sh completion
./test_llm.sh stream

# Python tests (auto-setup)
python3 test_client.py
python3 test_stream.py
python3 load_test.py

# With options
python3 test_client.py --requests 50
python3 test_stream.py --verbose
python3 load_test.py --requests 100 --concurrent 10

# Smart runner
./run_test.sh quick
./run_test.sh stream
./run_test.sh load
```

## 🎯 Success Criteria

- [ ] All tests pass
- [ ] Success rate >95%
- [ ] Response time <3s
- [ ] Resources stable
- [ ] No errors in logs

**Ready for production!** 🚀

---

**For detailed steps:** See [COMPLETE_TESTING_STEPS.md](COMPLETE_TESTING_STEPS.md)  
**For checklist:** See [TEST_CHECKLIST.md](TEST_CHECKLIST.md)
