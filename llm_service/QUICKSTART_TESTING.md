# Testing Quick Start

Get started testing your LLM service in under 2 minutes.

## Prerequisites

Your LLM service must be running:
```bash
./llm_manager.sh start
```

## Option 1: Shell Tests (Fastest - No Installation)

```bash
# Run all quick tests
./test_llm.sh quick

# Or test individual endpoints
./test_llm.sh health      # Check service health
./test_llm.sh completion  # Test completion
./test_llm.sh stream      # Test streaming
```

**Done!** You've tested your LLM service.

## Option 2: Python Tests (Recommended - Auto Setup)

**No manual installation needed!** The test scripts automatically:
- ✅ Create a virtual environment
- ✅ Install dependencies
- ✅ Run your tests

### Just run any test script:
```bash
# Comprehensive test suite (auto-installs dependencies first time)
python3 test_client.py

# Streaming tests
python3 test_stream.py

# Load testing
python3 load_test.py --requests 50 --concurrent 10
```

**First run:** Takes ~30 seconds to setup environment  
**Subsequent runs:** Instant, uses existing environment

### Alternative: Use the smart runner
```bash
# Quick shortcuts
./run_test.sh quick       # Run test_client.py
./run_test.sh stream      # Run test_stream.py
./run_test.sh load        # Run load_test.py
./run_test.sh examples    # Run examples

# Or run any script
./run_test.sh test_client.py --requests 50
./run_test.sh load_test.py --requests 100 --concurrent 10
```

**Done!** You now have detailed performance metrics.

## What Each Test Does

| Test | What It Does | Run Time |
|------|--------------|----------|
| `test_llm.sh quick` | Health + basic functionality | ~10 sec |
| `test_client.py` | All endpoints + performance metrics | ~30 sec |
| `test_stream.py` | Streaming with detailed metrics | ~20 sec |
| `load_test.py` | High-volume load testing | ~1-2 min |

## Quick Examples

### Test Different Service
```bash
# Shell
./test_llm.sh --url http://192.168.1.100:8000 quick

# Python
python3 test_client.py --url http://192.168.1.100:8000
```

### Test With Custom Prompt
```bash
# Shell
./test_llm.sh completion --prompt "What is AI?" --max-tokens 100

# Python
python3 test_stream.py --custom-prompt "Explain quantum physics" --max-tokens 200
```

### Run Heavy Load Test
```bash
python3 load_test.py --requests 500 --concurrent 25 --ramp-up 10
```

## Interpreting Results

### Success Indicators ✅
- Success rate: 95-100%
- Response time: < 2 seconds (varies by model)
- No timeout errors
- Tokens generating smoothly

### Problem Indicators ❌
- Success rate: < 90%
- Response time: > 5 seconds
- Frequent timeouts
- Connection errors

## Troubleshooting

### "Connection refused" error
```bash
# Check if service is running
./llm_manager.sh status

# Start if needed
./llm_manager.sh start
```

### Tests are slow
```bash
# Reduce concurrent requests
python3 test_client.py --requests 10 --concurrent 2

# Check service logs
./llm_manager.sh logs
```

### Timeout errors
```bash
# Increase timeout
python3 load_test.py --requests 50 --timeout 300

# Check GPU memory
nvidia-smi
```

## Next Steps

1. ✅ Run quick tests to verify service works
2. ✅ Run comprehensive tests to get performance metrics
3. ✅ Run load tests to find capacity limits
4. 📖 Read [TESTING.md](TESTING.md) for detailed documentation
5. 📖 Check [TEST_EXAMPLES.md](TEST_EXAMPLES.md) for more examples

## Common Commands Cheat Sheet

```bash
# Quick health check
./test_llm.sh health

# Quick smoke test
./test_llm.sh quick

# Comprehensive test
python3 test_client.py

# Streaming test with output
python3 test_stream.py --verbose

# Light load test
python3 load_test.py --requests 50 --concurrent 5

# Heavy load test
python3 load_test.py --requests 1000 --concurrent 50

# Run examples
python3 example_usage.py

# Run specific example
python3 example_usage.py --example 1
```

## Need Help?

- **Detailed docs**: See [TESTING.md](TESTING.md)
- **Examples**: See [TEST_EXAMPLES.md](TEST_EXAMPLES.md)
- **Service logs**: Run `./llm_manager.sh logs`
- **Service status**: Run `./llm_manager.sh status`

