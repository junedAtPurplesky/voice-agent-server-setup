# LLM Service Testing Guide

Comprehensive testing suite for the LLM service with multiple test clients and approaches.

## Quick Start

### 1. Basic Shell Testing (No Dependencies)

```bash
# Run quick test suite
./test_llm.sh quick

# Test individual endpoints
./test_llm.sh health
./test_llm.sh completion
./test_llm.sh chat
./test_llm.sh stream
```

### 2. Python Test Clients (Recommended - Auto Setup)

**No manual installation needed!** Just run the tests:

```bash
# First run automatically creates venv and installs dependencies
python3 test_client.py

# Subsequent runs are instant
python3 test_client.py --url http://127.0.0.1:8000 --requests 50 --concurrent 10
```

**Alternative: Use the smart runner:**
```bash
./run_test.sh quick       # Run comprehensive tests
./run_test.sh stream      # Run streaming tests
./run_test.sh load        # Run load tests

# With parameters
./run_test.sh test_client.py --requests 100
./run_test.sh load_test.py --requests 500 --concurrent 25
```

**How it works:**
- 🔍 Detects if dependencies are available
- 📦 Creates `.test_venv` directory (first run only)
- ⬆️ Installs required packages (first run only)
- 🚀 Runs your tests
- ⚡ Subsequent runs use existing environment

## Test Clients Overview

### 1. `test_llm.sh` - Quick Shell Tests
Lightweight bash script for quick testing without Python dependencies.

**Features:**
- Health check
- Basic completion test
- Chat completion test
- Streaming test
- No external dependencies (just curl and jq)

**Usage:**
```bash
# Quick test suite
./test_llm.sh quick

# Custom URL
./test_llm.sh --url http://192.168.1.100:8000 health

# Custom prompt
./test_llm.sh completion --prompt "What is AI?" --max-tokens 100

# Streaming
./test_llm.sh stream --prompt "Write a poem"
```

### 2. `test_client.py` - Comprehensive Test Suite
Complete test client covering all functionality with detailed metrics.

**Features:**
- ✅ Health checks
- ✅ Completion endpoint testing
- ✅ Chat completion testing
- ✅ Streaming endpoint testing
- ✅ Concurrent request testing
- ✅ Performance metrics (response time, tokens/sec)
- ✅ Success rate tracking
- ✅ Statistical analysis

**Usage:**
```bash
# Run all tests with defaults
python3 test_client.py

# Custom configuration
python3 test_client.py \
    --url http://127.0.0.1:8000 \
    --requests 30 \
    --concurrent 5

# Test remote service
python3 test_client.py --url http://192.168.1.100:8000
```

**Example Output:**
```
🏥 Testing Service Health...
✅ Service is healthy (Response time: 0.123s)

1️⃣  Testing Basic Completion...
✅ Completion test passed (1.234s, 47 tokens)

2️⃣  Testing Chat Completion...
✅ Chat completion test passed (1.456s, 89 tokens)

3️⃣  Testing Streaming...
✅ Streaming test passed (2.345s, 156 chunks)

4️⃣  Running Performance Test...
============================================================
📊 PERFORMANCE METRICS
============================================================

📈 Request Statistics:
  Total Requests:    20
  Successful:        20
  Failed:            0
  Success Rate:      100.00%

⏱️  Response Times (seconds):
  Min:               0.845s
  Max:               2.134s
  Mean:              1.234s
  Median:            1.198s
  Std Dev:           0.234s

🎯 Token Statistics:
  Total Tokens:      945
  Avg per Request:   47.3
  Throughput:        38.42 tokens/s
```

### 3. `test_stream.py` - Streaming-Focused Testing
Specialized client for testing streaming capabilities in detail.

**Features:**
- 🌊 Detailed streaming metrics
- ⚡ Time to first token measurement
- 📦 Chunk timing analysis
- 📊 Throughput measurements
- 💬 Both completion and chat streaming
- 👁️ Real-time output display (optional)

**Usage:**
```bash
# Run default streaming tests
python3 test_stream.py

# Custom number of tests
python3 test_stream.py --num-tests 10

# With real-time output
python3 test_stream.py --verbose

# Custom prompt
python3 test_stream.py --custom-prompt "Write a long story" --max-tokens 500

# Adjust max tokens
python3 test_stream.py --max-tokens 300
```

**Example Output:**
```
============================================================
🎯 Prompt: Write a short poem about technology...
============================================================

[Real-time streaming output if --verbose]

📊 Stream 1 Results:
────────────────────────────────────────────────────────────
✅ Status:                 Success
⏱️  Total Time:             2.456s
🚀 Time to First Token:    0.234s
📦 Chunks Received:        143
📝 Total Text Length:      567 chars
⚡ Throughput:             58.23 chunks/s
⏲️  Avg Chunk Time:        16.8ms
⏲️  Min Chunk Time:        12.3ms
⏲️  Max Chunk Time:        45.6ms
────────────────────────────────────────────────────────────

============================================================
📈 STREAMING TEST SUMMARY
============================================================
Total Tests:          5
Successful:           5
Failed:               0
Success Rate:         100.0%

⏱️  Averages:
  Total Time:         2.234s
  Time to First:      0.245s
  Chunks per Stream:  138.4
  Throughput:         56.78 chunks/s
============================================================
```

### 4. `load_test.py` - Load & Performance Testing
High-volume testing for measuring service capacity under load.

**Features:**
- 🚀 High-volume request testing
- 📊 Concurrent user simulation
- ⏱️ Detailed latency metrics (P50, P95, P99)
- 📈 Throughput measurements
- 🔄 Ramp-up support
- ❌ Error tracking and categorization
- 📡 HTTP status code analysis

**Usage:**
```bash
# Basic load test (100 requests, 10 concurrent)
python3 load_test.py

# Heavy load test
python3 load_test.py --requests 1000 --concurrent 50

# With ramp-up (gradually increase load)
python3 load_test.py --requests 500 --concurrent 25 --ramp-up 10

# Test streaming under load
python3 load_test.py --requests 100 --concurrent 10 --stream

# Custom prompt and tokens
python3 load_test.py \
    --requests 200 \
    --concurrent 20 \
    --max-tokens 150 \
    --prompt "Custom test prompt"

# Adjust timeout for slower responses
python3 load_test.py --requests 50 --timeout 180
```

**Example Output:**
```
======================================================================
🚀 STARTING LOAD TEST
======================================================================
Total Requests:       100
Concurrent Users:     10
Ramp-up Time:         0.0s
Max Tokens:           100
Streaming:            False
======================================================================

🔄 Batch 1/10: Sending 10 requests...
   ✓ Completed 10/100 (10/10 successful)
🔄 Batch 2/10: Sending 10 requests...
   ✓ Completed 20/100 (10/10 successful)
...

======================================================================
📊 LOAD TEST REPORT
======================================================================

📈 SUMMARY
──────────────────────────────────────────────────────────────────────
Total Requests:        100
Successful:            98
Failed:                2
Success Rate:          98.00%
Total Time:            15.67s
Throughput:            6.25 req/s

⏱️  RESPONSE TIMES (seconds)
──────────────────────────────────────────────────────────────────────
Min:                   0.845s
Max:                   3.234s
Mean:                  1.567s
Median (P50):          1.456s
P95:                   2.345s
P99:                   2.987s
Std Dev:               0.456s

🎯 TOKEN STATISTICS
──────────────────────────────────────────────────────────────────────
Total Tokens:          4567
Avg per Request:       46.6
Throughput:            291.34 tokens/s

📡 HTTP STATUS CODES
──────────────────────────────────────────────────────────────────────
200:                      98 requests
503:                      2 requests

❌ ERRORS
──────────────────────────────────────────────────────────────────────
HTTP 503                                          2

======================================================================
```

## Test Scenarios

### Basic Functionality Tests
```bash
# Test all endpoints
python3 test_client.py --requests 10 --concurrent 2

# Test only streaming
python3 test_stream.py --num-tests 5
```

### Performance Benchmarking
```bash
# Measure baseline performance
python3 load_test.py --requests 100 --concurrent 5

# Find concurrent request limit
python3 load_test.py --requests 50 --concurrent 10
python3 load_test.py --requests 50 --concurrent 20
python3 load_test.py --requests 50 --concurrent 50
```

### Stress Testing
```bash
# High volume
python3 load_test.py --requests 1000 --concurrent 50 --ramp-up 30

# Long generation
python3 test_stream.py --max-tokens 2000 --num-tests 10
```

### Latency Testing
```bash
# Test time to first token
python3 test_stream.py --verbose --num-tests 20

# Analyze response time distribution
python3 load_test.py --requests 200 --concurrent 10
```

## Interpreting Results

### Response Time Metrics
- **Min/Max**: Range of response times
- **Mean**: Average response time
- **Median (P50)**: 50% of requests complete faster
- **P95**: 95% of requests complete faster (good SLA metric)
- **P99**: 99% of requests complete faster (tail latency)
- **Std Dev**: Consistency of response times (lower is better)

### Throughput Metrics
- **Requests/sec**: How many requests the service can handle
- **Tokens/sec**: Token generation rate
- **Chunks/sec**: Streaming chunk delivery rate

### Quality Metrics
- **Success Rate**: Percentage of successful requests
- **Time to First Token**: Latency before streaming starts
- **Error Rate**: Percentage of failed requests

## Troubleshooting

### Service Not Responding
```bash
# Check if service is running
curl http://127.0.0.1:8000/v1/models

# Check service status
cd /path/to/llm_service
./llm_manager.sh status

# View logs
./llm_manager.sh logs
```

### Test Connection Issues
```bash
# Test with explicit URL
python3 test_client.py --url http://127.0.0.1:8000

# Test from different network
python3 test_client.py --url http://192.168.1.100:8000

# Check port is accessible
nc -zv 127.0.0.1 8000
```

### Timeout Errors
```bash
# Increase timeout for load test
python3 load_test.py --timeout 300

# Reduce concurrent requests
python3 load_test.py --concurrent 5

# Reduce token generation
python3 test_client.py --requests 10 --concurrent 2
```

### High Error Rates
- Check service logs for errors
- Reduce concurrent requests
- Check GPU memory usage
- Verify model configuration

## CI/CD Integration

### Quick Smoke Test
```bash
#!/bin/bash
# smoke_test.sh
./test_llm.sh quick || exit 1
```

### Comprehensive Test
```bash
#!/bin/bash
# full_test.sh
python3 test_client.py --requests 20 --concurrent 5 || exit 1
python3 test_stream.py --num-tests 5 || exit 1
python3 load_test.py --requests 50 --concurrent 10 || exit 1
```

### Performance Regression Test
```bash
#!/bin/bash
# Store baseline metrics and compare
python3 load_test.py --requests 100 --concurrent 10 > current_metrics.txt
# Compare with baseline_metrics.txt
```

## Advanced Usage

### Custom Test Scenarios
Create custom test scripts by importing the test clients:

```python
from test_client import LLMTestClient

async def custom_test():
    client = LLMTestClient(base_url="http://127.0.0.1:8000")
    
    # Your custom test logic
    result = await client.test_completion(
        prompt="Custom prompt",
        max_tokens=100
    )
    
    print(f"Response time: {result.response_time}s")

asyncio.run(custom_test())
```

### Environment Variables
```bash
# Set default URL
export LLM_URL=http://192.168.1.100:8000
./test_llm.sh quick

# Or use directly
LLM_URL=http://192.168.1.100:8000 ./test_llm.sh quick
```

## Best Practices

1. **Start Small**: Begin with quick tests before load testing
2. **Monitor Service**: Keep an eye on service logs during tests
3. **Gradual Load**: Use `--ramp-up` for realistic load patterns
4. **Baseline First**: Establish baseline metrics for comparison
5. **Test Regularly**: Run tests after configuration changes
6. **Document Results**: Keep records of performance metrics
7. **Test Different Scenarios**: Vary prompts, token lengths, etc.

## Requirements

### Shell Tests
- `curl` - HTTP client
- `jq` - JSON processor
- `bc` - Calculator for timing

### Python Tests
- Python 3.7+
- **No manual installation needed!** Dependencies auto-install on first run
- If you want to manually install: `pip install -r requirements.txt`

**What happens on first run:**
1. Script detects missing dependencies
2. Creates `.test_venv` virtual environment
3. Installs `httpx` and other requirements
4. Runs your test
5. Future runs use the existing environment

## Support

For issues or questions:
1. Check service logs: `./llm_manager.sh logs`
2. Verify service status: `./llm_manager.sh status`
3. Review configuration: `cat llm_config.sh`
4. Test connectivity: `./test_llm.sh health`

