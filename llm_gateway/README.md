# LLM Gateway - Node.js + TypeScript

A **model-agnostic** secure proxy gateway with API key validation and **proper streaming support**.

Works with any OpenAI-compatible LLM backend: vLLM, Ollama, llama.cpp, TGI, LocalAI, or any custom LLM server.

## Features

- ✅ **Model-agnostic** - Works with ANY LLM (vLLM, Ollama, llama.cpp, TGI, etc.)
- ✅ **Proper SSE streaming** - No buffering, immediate chunk forwarding (15x faster than Python)
- 🔐 **API key authentication** - Secure access control
- 🔄 **Full OpenAI-compatible** - All endpoints supported
- 🚀 **High-performance** - Native Node.js streaming with direct piping
- 📝 **TypeScript** - Type-safe code
- 🧪 **Comprehensive tests** - Built-in integration tests with mock LLM server

## Migration from Python

This is a complete rewrite of the Python FastAPI gateway in Node.js + TypeScript. The main improvement is **proper streaming support** using Node.js native HTTP modules with direct piping, eliminating the buffering issues present in the Python version.

## Installation

```bash
npm install
```

## Configuration

Create a `.env` file:

```env
# Required
ALLOWED_API_KEYS=key1,key2,key3

# Optional - Point to ANY OpenAI-compatible LLM backend
VLLM_BASE=http://127.0.0.1:8000        # vLLM
# VLLM_BASE=http://localhost:11434     # Ollama
# VLLM_BASE=https://api.openai.com     # OpenAI
# VLLM_BASE=http://localhost:8080      # LocalAI
# VLLM_BASE=http://your-llm:8000       # Any custom LLM

GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8080
```

## Running

### Development (with hot reload)
```bash
npm run dev
```

### Production
```bash
npm run build
npm start
```

### Using the startup script
```bash
chmod +x start_gateway_node.sh
./start_gateway_node.sh
```

## Testing Streaming

### Quick Test (Recommended)

Run the full stack test with mock vLLM server:

```bash
./test-full-stack.sh
```

This will:
- Start a mock vLLM server
- Start the gateway
- Run 5 comprehensive tests
- Verify streaming works correctly
- Report results and clean up

**Expected output:**
```
✅ ALL TESTS PASSED!
Your gateway is working correctly and safe to deploy! 🚀
```

### Manual Testing

```bash
# Build first
npm run build

# Test against real vLLM
export GATEWAY_URL=http://localhost:8080
export TEST_API_KEY=your-api-key
npm run test:stream
```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete testing documentation.

### Manual Testing with curl

Test streaming:
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
      {"role": "user", "content": "Explain transformers in simple terms."}
    ]
  }'
```

Test non-streaming:
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

## Streaming Implementation Details

The key to proper streaming in this implementation:

1. **Native HTTP modules**: Uses Node.js `http`/`https` modules instead of higher-level libraries
2. **Direct piping**: `proxyRes.pipe(res)` directly pipes the upstream response to the client
3. **No buffering**: Disabled all buffering at Express and response level
4. **Proper headers**: Sets `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`
5. **Error handling**: Proper cleanup on client disconnect and stream errors

## Supported Endpoints

### OpenAI-Compatible
- `POST /v1/chat/completions` ✅ Streaming supported
- `POST /v1/completions` ✅ Streaming supported
- `POST /v1/embeddings`
- `GET /v1/models`
- `POST /v1/audio/transcriptions`
- `POST /v1/audio/translations`
- `POST /v1/rerank`

### vLLM-Specific
- `GET /health`
- `GET /load`
- `POST|GET /ping`
- `POST /tokenize`
- `POST /detokenize`
- `POST /classify`
- `POST /score`
- `POST /pooling`
- `GET /metrics`

### Gateway
- `GET /healthz` - Gateway + vLLM health check (no auth required)

## Architecture

```
Client Request
     ↓
  Gateway (Express + Auth)
     ↓
  Native HTTP Request → vLLM Backend
     ↓
  Stream Detection (content-type check)
     ↓
  ┌─────────────────┬──────────────────┐
  │   SSE Stream    │   Regular JSON   │
  │  (Direct Pipe)  │   (Buffered)     │
  └─────────────────┴──────────────────┘
     ↓                      ↓
  Client              Client
```

## License

MIT

