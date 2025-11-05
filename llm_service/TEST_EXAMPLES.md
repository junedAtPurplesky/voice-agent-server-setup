# LLM Service Test Examples

Quick reference for common testing scenarios.

## Quick Tests

### Basic Health Check
```bash
# Shell
./test_llm.sh health

# Or with curl
curl http://127.0.0.1:8000/v1/models
```

### Run All Quick Tests
```bash
./test_llm.sh quick
```

## Python Test Examples

### Basic Testing

**Simple test run:**
```bash
python3 test_client.py
```

**Custom parameters:**
```bash
python3 test_client.py \
  --url http://127.0.0.1:8000 \
  --requests 30 \
  --concurrent 5
```

### Streaming Tests

**Basic streaming test:**
```bash
python3 test_stream.py
```

**Verbose mode (see output in real-time):**
```bash
python3 test_stream.py --verbose
```

**Custom prompt:**
```bash
python3 test_stream.py \
  --custom-prompt "Write a detailed explanation of neural networks" \
  --max-tokens 500
```

**Multiple streaming tests:**
```bash
python3 test_stream.py --num-tests 20
```

### Load Testing

**Light load test:**
```bash
python3 load_test.py --requests 50 --concurrent 5
```

**Medium load test:**
```bash
python3 load_test.py --requests 200 --concurrent 20
```

**Heavy load test with ramp-up:**
```bash
python3 load_test.py \
  --requests 1000 \
  --concurrent 50 \
  --ramp-up 30
```

**Streaming load test:**
```bash
python3 load_test.py \
  --requests 100 \
  --concurrent 10 \
  --stream
```

**Long token generation:**
```bash
python3 load_test.py \
  --requests 50 \
  --max-tokens 500 \
  --timeout 300
```

## Shell Test Examples

### Completion Tests

**Basic:**
```bash
./test_llm.sh completion
```

**Custom prompt:**
```bash
./test_llm.sh completion \
  --prompt "What is quantum computing?" \
  --max-tokens 200
```

### Chat Tests

**Basic:**
```bash
./test_llm.sh chat
```

**Custom message:**
```bash
./test_llm.sh chat \
  --message "Explain machine learning to a beginner" \
  --max-tokens 150
```

### Streaming Tests

**Basic:**
```bash
./test_llm.sh stream
```

**Custom:**
```bash
./test_llm.sh stream \
  --prompt "Write a science fiction story" \
  --max-tokens 300
```

## Testing Different Endpoints

### Test Remote Service
```bash
# Python
python3 test_client.py --url http://192.168.1.100:8000

# Shell
./test_llm.sh --url http://192.168.1.100:8000 quick
```

### Test Different Port
```bash
python3 test_client.py --url http://127.0.0.1:8080
```

## Performance Testing Scenarios

### Find Maximum Concurrent Requests

**Start small:**
```bash
python3 load_test.py --requests 50 --concurrent 5
```

**Gradually increase:**
```bash
python3 load_test.py --requests 50 --concurrent 10
python3 load_test.py --requests 50 --concurrent 20
python3 load_test.py --requests 50 --concurrent 50
python3 load_test.py --requests 50 --concurrent 100
```

### Measure Baseline Performance

**Consistent test:**
```bash
# Run multiple times and compare
for i in {1..5}; do
  echo "Run $i:"
  python3 load_test.py --requests 100 --concurrent 10
  sleep 30
done
```

### Test Under Different Loads

**Peak hours simulation:**
```bash
python3 load_test.py \
  --requests 500 \
  --concurrent 50 \
  --ramp-up 20
```

**Off-peak simulation:**
```bash
python3 load_test.py \
  --requests 100 \
  --concurrent 5
```

## Continuous Testing

### Smoke Test Script
```bash
#!/bin/bash
# smoke_test.sh
echo "Running smoke tests..."
./test_llm.sh quick
if [ $? -eq 0 ]; then
  echo "✅ Smoke tests passed"
  exit 0
else
  echo "❌ Smoke tests failed"
  exit 1
fi
```

### Full Test Suite
```bash
#!/bin/bash
# full_test_suite.sh
echo "=== Running Full Test Suite ==="

echo -e "\n1. Basic Tests"
python3 test_client.py --requests 20 --concurrent 5 || exit 1

echo -e "\n2. Streaming Tests"
python3 test_stream.py --num-tests 10 || exit 1

echo -e "\n3. Load Tests"
python3 load_test.py --requests 100 --concurrent 10 || exit 1

echo -e "\n✅ All tests passed!"
```

### Performance Monitoring
```bash
#!/bin/bash
# monitor_performance.sh
while true; do
  echo "=== $(date) ==="
  python3 load_test.py --requests 50 --concurrent 10
  sleep 300  # Wait 5 minutes
done
```

## Programmatic Usage

### Custom Test Script

**basic_custom_test.py:**
```python
#!/usr/bin/env python3
import asyncio
from test_client import LLMTestClient

async def main():
    # Initialize client
    client = LLMTestClient(base_url="http://127.0.0.1:8000")
    
    # Test health
    healthy = await client.test_health()
    if not healthy:
        print("Service not available")
        return
    
    # Test completion
    result = await client.test_completion(
        prompt="What is AI?",
        max_tokens=100
    )
    
    if result.success:
        print(f"✅ Test passed in {result.response_time:.2f}s")
        print(f"Generated {result.tokens_generated} tokens")
    else:
        print(f"❌ Test failed: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

**run_multiple_tests.py:**
```python
#!/usr/bin/env python3
import asyncio
from test_client import LLMTestClient

async def main():
    client = LLMTestClient()
    
    # Test different prompts
    prompts = [
        "Explain artificial intelligence",
        "What is machine learning?",
        "How do neural networks work?",
        "What is deep learning?",
    ]
    
    for prompt in prompts:
        result = await client.test_completion(prompt=prompt)
        print(f"{prompt[:30]}... - {result.response_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

**streaming_custom_test.py:**
```python
#!/usr/bin/env python3
import asyncio
from test_stream import StreamingTestClient

async def main():
    client = StreamingTestClient()
    
    # Test streaming with metrics
    metrics = await client.test_stream_completion(
        prompt="Write a poem about coding",
        max_tokens=200,
        verbose=True
    )
    
    client.print_metrics(metrics, "Coding Poem Test")

if __name__ == "__main__":
    asyncio.run(main())
```

## Environment-Specific Tests

### Development Environment
```bash
export LLM_URL=http://localhost:8000
python3 test_client.py --requests 10 --concurrent 2
```

### Staging Environment
```bash
export LLM_URL=http://staging.example.com:8000
python3 load_test.py --requests 100 --concurrent 10
```

### Production Environment
```bash
export LLM_URL=https://api.example.com
python3 load_test.py --requests 1000 --concurrent 50 --ramp-up 30
```

## Debugging Failed Tests

### Verbose Output
```bash
# Shell tests already show full output
./test_llm.sh completion

# Python - use streaming verbose mode
python3 test_stream.py --verbose
```

### Test Specific Endpoint
```bash
# Just health
curl -v http://127.0.0.1:8000/v1/models

# Just completion
curl -X POST http://127.0.0.1:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "default", "prompt": "test", "max_tokens": 10}'
```

### Check Service Logs
```bash
# While running tests in another terminal
./llm_manager.sh logs
```

## CI/CD Pipeline Examples

### GitHub Actions
```yaml
name: LLM Service Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd llm_service
          pip install -r requirements.txt
      
      - name: Start LLM service
        run: |
          cd llm_service
          ./llm_manager.sh setup
          ./llm_manager.sh start
          sleep 30  # Wait for service to be ready
      
      - name: Run tests
        run: |
          cd llm_service
          python3 test_client.py --requests 20 --concurrent 5
          python3 test_stream.py --num-tests 5
      
      - name: Run load test
        run: |
          cd llm_service
          python3 load_test.py --requests 50 --concurrent 10
```

### GitLab CI
```yaml
test:
  stage: test
  script:
    - cd llm_service
    - pip install -r requirements.txt
    - ./llm_manager.sh setup
    - ./llm_manager.sh start
    - sleep 30
    - python3 test_client.py --requests 20
    - python3 load_test.py --requests 50
```

## Tips

1. **Start small**: Begin with `--requests 10 --concurrent 2`
2. **Monitor service**: Watch logs during testing
3. **Gradual increases**: Double concurrent requests gradually
4. **Use ramp-up**: For realistic load testing
5. **Check metrics**: Focus on P95/P99 latencies
6. **Test streaming separately**: Different performance characteristics
7. **Baseline first**: Establish normal performance metrics
8. **Document results**: Keep track of performance over time

## Common Issues

### Timeout Errors
```bash
# Increase timeout
python3 load_test.py --requests 50 --timeout 300
```

### Connection Refused
```bash
# Check service is running
./llm_manager.sh status

# Check correct URL
./test_llm.sh --url http://127.0.0.1:8000 health
```

### Out of Memory (Service Side)
```bash
# Reduce concurrent requests
python3 load_test.py --requests 50 --concurrent 5

# Reduce token generation
python3 test_client.py --requests 20 --concurrent 3
```

## Next Steps

1. Start with shell tests: `./test_llm.sh quick`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run comprehensive tests: `python3 test_client.py`
4. Test streaming: `python3 test_stream.py`
5. Measure load capacity: `python3 load_test.py`
6. Review [TESTING.md](TESTING.md) for detailed documentation

