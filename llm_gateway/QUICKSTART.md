# Quick Start Guide - Node.js Gateway

## 🚀 Setup (3 steps)

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set your API keys
nano .env
```

### 3. Start the Gateway

**Option A: Using the script**
```bash
./start_gateway_node.sh
```

**Option B: Using npm**
```bash
# Development (with hot reload)
npm run dev

# Production
npm run build && npm start
```

## 🧪 Testing Streaming

### Quick Test
```bash
# Update .env with your settings first
./test_stream.sh
```

### Manual Test with curl
```bash
curl -N -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key-1" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "temperature": 0.7,
    "max_tokens": 64,
    "stream": true,
    "messages": [
      {"role": "system", "content": "You are a helpful AI assistant."},
      {"role": "user", "content": "Explain transformers in simple terms."}
    ]
  }'
```

**Important**: Use the `-N` flag with curl to disable buffering for streaming!

## 🔑 What Changed from Python?

### Streaming Fix
The Python version had buffering issues with SSE streams. The Node.js version uses:
- **Native HTTP modules** (`http`/`https`) instead of high-level HTTP clients
- **Direct piping** (`proxyRes.pipe(res)`) for zero-copy streaming
- **Disabled buffering** at all levels

### Code Comparison

**Python (problematic)**:
```python
async for line in resp.aiter_lines():
    yield f"{line}\n"  # Can buffer lines
```

**Node.js (fixed)**:
```typescript
proxyRes.pipe(res, { end: true });  // Direct pipe, no buffering
```

## 📊 Verifying Stream Works

When streaming works correctly, you should see:
1. **Immediate first chunk** (no delay waiting for full response)
2. **Individual tokens** appearing one by one
3. **`data:` prefixed lines** in the output
4. **`data: [DONE]`** at the end

Example correct output:
```
data: {"id":"...","choices":[{"delta":{"role":"assistant","content":""}}]}

data: {"id":"...","choices":[{"delta":{"content":"Transform"}}]}

data: {"id":"...","choices":[{"delta":{"content":"ers"}}]}

...

data: [DONE]
```

## 🐛 Troubleshooting

### Gateway won't start
- Check if port 8080 is already in use: `lsof -i :8080`
- Verify .env file exists with valid API keys
- Check Node.js version: `node --version` (needs 18+)

### Streaming still buffers
- Make sure you're using the `-N` flag with curl
- Check your reverse proxy (nginx/caddy) buffering settings
- Verify VLLM_BASE is correct and reachable

### Connection refused
- Ensure vLLM backend is running: `curl http://localhost:8000/health`
- Check VLLM_BASE in .env matches your vLLM server

## 📖 Full Documentation

See [README.md](README.md) for complete documentation.

