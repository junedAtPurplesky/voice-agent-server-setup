# Testing Guide

## Overview

This guide covers how to test the gateway, especially the streaming functionality which was the main reason for migration from Python.

## Quick Test

```bash
# 1. Start the gateway
./start_gateway_node.sh

# 2. Run automated test (in another terminal)
./test_stream.sh
```

## Detailed Testing

### 1. Basic Streaming Test

Test that streaming works:

```bash
curl -N -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "temperature": 0.7,
    "max_tokens": 64,
    "stream": true,
    "messages": [
      {"role": "system", "content": "You are a helpful AI assistant."},
      {"role": "user", "content": "Count from 1 to 10."}
    ]
  }'
```

**What to look for:**
- ✅ Immediate first chunk (< 50ms)
- ✅ Progressive output (tokens appear one by one)
- ✅ Each line starts with `data:`
- ✅ Ends with `data: [DONE]`

**Bad signs:**
- ❌ Long delay before first output
- ❌ All text appears at once
- ❌ No `data:` prefix
- ❌ Incomplete stream

### 2. Non-Streaming Test

Test regular JSON responses:

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "temperature": 0.7,
    "max_tokens": 32,
    "stream": false,
    "messages": [
      {"role": "user", "content": "Say hello"}
    ]
  }'
```

**Expected output:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }]
}
```

### 3. Authentication Test

Test that authentication works:

```bash
# Valid key - should work
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer valid-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": []}'

# Invalid key - should fail with 403
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": []}'

# No key - should fail with 401
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": []}'
```

### 4. Health Check Test

```bash
# Gateway health
curl http://localhost:8080/healthz

# Expected output:
{
  "gateway": {"gateway": "ok"},
  "vllm": {...},
  "vllm_status": "ok"
}
```

### 5. Load Test

Test concurrent streaming requests:

```bash
# Simple load test with 10 concurrent requests
for i in {1..10}; do
  (
    curl -N -X POST http://localhost:8080/v1/chat/completions \
      -H "Authorization: Bearer your-api-key" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
        "stream": true,
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "Test '$i'"}]
      }' > /tmp/test-$i.log 2>&1
  ) &
done

wait
echo "All tests complete. Check /tmp/test-*.log"
```

### 6. Client Disconnect Test

Test that the gateway properly handles client disconnects:

```bash
# Start streaming and interrupt with Ctrl+C after 1 second
timeout 1 curl -N -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "stream": true,
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "Write a long essay"}]
  }'
```

**Check gateway logs:**
- Should see: `[Stream] Client disconnected, destroying proxy stream`
- No memory leaks or hanging connections

### 7. Error Handling Test

Test various error conditions:

```bash
# Invalid JSON
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d 'invalid json'

# Invalid endpoint
curl -X POST http://localhost:8080/v1/invalid/endpoint \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{}'

# Backend down (stop vLLM first)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": []}'
```

## Automated Test Suite

The built-in test script (`test_stream.sh`) runs comprehensive tests:

```bash
./test_stream.sh
```

**What it tests:**
1. Streaming response
2. Non-streaming response
3. Chunk counting
4. Content assembly
5. [DONE] marker
6. Response timing

**Example output:**
```
🧪 Testing Streaming...

Status: 200
Headers: {
  "content-type": "text/event-stream",
  "cache-control": "no-cache",
  "connection": "keep-alive"
}

--- Stream Output ---

data: {"id":"...","choices":[{"delta":{"role":"assistant","content":""}}]}
data: {"id":"...","choices":[{"delta":{"content":"Transform"}}]}
...
data: [DONE]

--- Stream Complete ---
Total chunks received: 45
Total bytes: 8192
Total data lines: 45

✅ Stream finished with [DONE] marker

📝 Assembled Content:
Transformers are complex artificial intelligence models...
```

## Performance Testing

### Measure First Chunk Latency

```bash
curl -w "\nTime to first byte: %{time_starttransfer}s\n" \
  -N -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "stream": true,
    "max_tokens": 64,
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

**Good**: < 0.05s (50ms)
**Bad**: > 0.2s (200ms)

### Compare Python vs Node.js

Run both simultaneously on different ports:

```bash
# Terminal 1: Python
GATEWAY_PORT=8080 ./start_gateway.sh

# Terminal 2: Node.js
GATEWAY_PORT=8081 ./start_gateway_node.sh

# Terminal 3: Compare
./compare-implementations.sh your-api-key 5
```

## Common Issues & Solutions

### Issue: No output until stream completes

**Cause**: Buffering somewhere in the chain

**Solutions:**
1. Use `curl -N` (disable buffering)
2. Check reverse proxy settings
3. Verify `Content-Type: text/event-stream` in response
4. Check for `X-Accel-Buffering: no` header

### Issue: "Connection refused"

**Cause**: vLLM backend not running

**Solutions:**
1. Check vLLM status: `curl http://localhost:8000/health`
2. Verify `VLLM_BASE` in `.env`
3. Check firewall/network settings

### Issue: "Invalid API key"

**Cause**: API key not configured or wrong

**Solutions:**
1. Check `.env` file: `cat .env | grep ALLOWED_API_KEYS`
2. Verify key matches: `echo $API_KEY`
3. Restart gateway after changing `.env`

### Issue: Incomplete streams

**Cause**: Client disconnect or backend error

**Solutions:**
1. Check gateway logs for errors
2. Check vLLM logs
3. Try lower `max_tokens`
4. Increase timeout

## Integration Testing

### With Python Client

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="your-api-key"
)

# Streaming
for chunk in client.chat.completions.create(
    model="Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    messages=[{"role": "user", "content": "Count to 5"}],
    stream=True
):
    print(chunk.choices[0].delta.content, end="", flush=True)
```

### With Node.js Client

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:8080/v1',
  apiKey: 'your-api-key',
});

async function main() {
  const stream = await client.chat.completions.create({
    model: 'Qwen/Qwen2.5-0.5B-Instruct-AWQ',
    messages: [{ role: 'user', content: 'Count to 5' }],
    stream: true,
  });
  
  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

main();
```

### With Curl Script

```bash
#!/bin/bash
# Save as test-integration.sh

curl -N -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
  "stream": true,
  "messages": [
    {"role": "user", "content": "Test message"}
  ]
}
EOF
```

## Continuous Testing

### With PM2 Monitoring

```bash
pm2 start dist/gateway.js --name llm-gateway
pm2 monit

# In another terminal, run tests
while true; do
  ./test_stream.sh
  sleep 10
done
```

### With Docker

```bash
# Build
docker build -t llm-gateway .

# Run
docker run -p 8080:8080 --env-file .env llm-gateway

# Test
docker run --network host curlimages/curl \
  -N -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer test-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "stream": true, "messages": []}'
```

## Success Criteria

Your gateway is working properly if:

- ✅ Streaming responses appear immediately (< 50ms first chunk)
- ✅ Tokens appear progressively, not all at once
- ✅ Non-streaming responses work correctly
- ✅ Authentication rejects invalid keys
- ✅ Health check shows both gateway and vLLM as healthy
- ✅ Client disconnects are handled gracefully
- ✅ No memory leaks during prolonged testing
- ✅ Concurrent requests work without issues

## Next Steps

Once testing is complete:

1. **Benchmark**: Compare with Python version
2. **Deploy**: Use PM2 or Docker for production
3. **Monitor**: Set up logging and metrics
4. **Scale**: Add load balancer if needed
5. **Optimize**: Tune based on your traffic patterns

## Resources

- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [MIGRATION.md](MIGRATION.md) - Migration from Python
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

