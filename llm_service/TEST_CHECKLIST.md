# Testing Checklist - Quick Reference

Print this and check off as you test!

## Pre-Testing Setup

- [ ] vLLM service is running: `./llm_manager.sh status`
- [ ] Port 8000 is accessible
- [ ] GPU is available (if using): `nvidia-smi`

## Phase 1: Quick Verification (2 minutes)

```bash
./test_llm.sh quick
```

- [ ] Health check passes
- [ ] Completion test passes
- [ ] Chat test passes
- [ ] Resources displayed (initial & final)
- [ ] No errors shown

**Expected:** All tests passed ✓

## Phase 2: Comprehensive Testing (1 minute)

```bash
python3 test_client.py
```

- [ ] Auto-setup completes (first run)
- [ ] Initial resources shown
- [ ] Model auto-detected
- [ ] Health check passes
- [ ] Completion test passes
- [ ] Chat test passes
- [ ] Streaming test passes
- [ ] Performance test completes
- [ ] Success rate 100% (or >95%)
- [ ] Final resources shown

**Expected:** All tests passed, success rate >95% ✓

## Phase 3: Streaming Tests (30 seconds)

```bash
python3 test_stream.py
```

- [ ] Initial resources shown
- [ ] 5 streaming tests complete
- [ ] Time to first token < 1s
- [ ] All tests successful
- [ ] Average throughput shown
- [ ] Final resources shown

**Expected:** All streams successful ✓

## Phase 4: Load Testing (1 minute)

```bash
python3 load_test.py --requests 50 --concurrent 5
```

- [ ] Initial resources shown
- [ ] All 50 requests sent
- [ ] Success rate >95%
- [ ] Mean response time <3s
- [ ] P95 latency <5s
- [ ] Token throughput >10 tokens/s
- [ ] No timeouts
- [ ] Final resources shown

**Expected:** Success rate >95%, acceptable latency ✓

## Phase 5: Medium Load (2 minutes)

```bash
python3 load_test.py --requests 100 --concurrent 10
```

- [ ] All requests complete
- [ ] Success rate >90%
- [ ] Latency acceptable
- [ ] Resources stable

**Expected:** Passes with good performance ✓

## Phase 6: Heavy Load (Optional, 2 minutes)

```bash
python3 load_test.py --requests 200 --concurrent 20
```

- [ ] Most requests succeed
- [ ] Service doesn't crash
- [ ] Resources within limits
- [ ] Recovery is fast

**Expected:** Stable under load ✓

## Resource Verification

Throughout testing, verify:

### GPU/VRAM
- [ ] VRAM usage displayed correctly
- [ ] GPU utilization shown
- [ ] Temperature monitored
- [ ] No OOM errors
- [ ] Usage is reasonable

### RAM
- [ ] RAM usage displayed
- [ ] Memory stable (no leaks)
- [ ] Percentage within limits

### CPU
- [ ] CPU usage displayed
- [ ] Not maxed out continuously
- [ ] Core count correct

## Final Checks

- [ ] Service still running: `./llm_manager.sh status`
- [ ] No errors in logs: `./llm_manager.sh logs | tail -20`
- [ ] Resources returned to baseline
- [ ] All test files ran successfully

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Quick shell test | ☐ Pass ☐ Fail | |
| Comprehensive test | ☐ Pass ☐ Fail | |
| Streaming test | ☐ Pass ☐ Fail | |
| Light load (50) | ☐ Pass ☐ Fail | |
| Medium load (100) | ☐ Pass ☐ Fail | |
| Heavy load (200) | ☐ Pass ☐ Fail | |

## Performance Metrics

Record your best results:

- Success Rate: ________%
- Mean Response Time: ________ seconds
- P95 Latency: ________ seconds
- Token Throughput: ________ tokens/sec
- Max Concurrent: ________ requests
- GPU VRAM Used: ________%
- RAM Used: ________%

## Issues Found

Document any issues:

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

## Sign-Off

- [ ] All critical tests passed
- [ ] Performance is acceptable
- [ ] Resources are stable
- [ ] Ready for deployment

**Tested by:** ________________  
**Date:** ________________  
**Environment:** ☐ Dev ☐ Staging ☐ Prod

---

**Next:** See COMPLETE_TESTING_STEPS.md for detailed instructions!
