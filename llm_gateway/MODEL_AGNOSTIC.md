# 🔄 Model-Agnostic Gateway

## Overview

This gateway is **completely model-agnostic**. It acts as a pure reverse proxy and doesn't care what model you're using. You can use it with:

- ✅ vLLM
- ✅ Ollama  
- ✅ llama.cpp
- ✅ Text Generation Inference (TGI)
- ✅ LocalAI
- ✅ Any OpenAI-compatible API
- ✅ Any custom LLM server

## How It Works

The gateway **forwards everything as-is**:

```
Client Request                Gateway                  Backend (Any LLM)
     │                           │                            │
     ├─ model: "llama-3.1"  ────►├────────────────────────────►│
     │                           │                            │
     │                           │  (Gateway doesn't care    │
     │                           │   what model you use)     │
     │                           │                            │
     │                           │◄────────────────────────────┤
     │◄──────────────────────────┤                            │
```

The gateway:
- ✅ **Never modifies** the model name
- ✅ **Never validates** the model name
- ✅ **Never hardcodes** any model
- ✅ **Simply forwards** the request to your backend

## Examples

### Using with Different Models

#### vLLM with Qwen

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

#### vLLM with Llama

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

#### Ollama

```bash
# Point gateway to Ollama
VLLM_BASE=http://localhost:11434 npm start

# Use any Ollama model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

#### OpenAI API

```bash
# Point gateway to OpenAI
VLLM_BASE=https://api.openai.com npm start

# Use any OpenAI model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

#### Custom Model

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -d '{
    "model": "my-custom-model-v2",
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

## Multi-Model Setup

### Single Gateway, Multiple Backends

You can run multiple gateways pointing to different backends:

```bash
# Gateway 1: vLLM with Qwen
GATEWAY_PORT=8080 VLLM_BASE=http://vllm-server:8000 npm start

# Gateway 2: Ollama
GATEWAY_PORT=8081 VLLM_BASE=http://localhost:11434 npm start

# Gateway 3: OpenAI
GATEWAY_PORT=8082 VLLM_BASE=https://api.openai.com npm start
```

Then clients choose which gateway:

```python
# Client code
import openai

# Use vLLM
client_vllm = openai.OpenAI(base_url="http://localhost:8080/v1", api_key="key")

# Use Ollama
client_ollama = openai.OpenAI(base_url="http://localhost:8081/v1", api_key="key")

# Use OpenAI
client_openai = openai.OpenAI(base_url="http://localhost:8082/v1", api_key="key")
```

### Load Balancing Multiple Models

Use nginx/caddy to route by model name:

```nginx
# nginx.conf
upstream vllm_qwen {
    server localhost:8001;
}

upstream vllm_llama {
    server localhost:8002;
}

server {
    listen 8080;
    
    location / {
        # Simple routing based on headers
        # (More complex routing would require inspecting JSON body)
        proxy_pass http://vllm_qwen;
    }
}
```

## Configuration

### Environment Variables

The **only** configuration needed:

```bash
# Required
ALLOWED_API_KEYS=key1,key2,key3

# Backend URL (any OpenAI-compatible API)
VLLM_BASE=http://your-llm-server:8000

# Optional
GATEWAY_PORT=8080
GATEWAY_HOST=0.0.0.0
```

**No model configuration needed!** ✅

## Testing with Different Models

### Mock Server

The mock vLLM server accepts any model name:

```bash
# Start mock server
npm run mock:vllm

# Test with any model name
curl -X POST http://localhost:8000/v1/chat/completions \
  -d '{
    "model": "any-model-name-works",
    "stream": true,
    "messages": [{"role": "user", "content": "Test"}]
  }'
```

### Integration Tests

Tests use generic model names:

```bash
./test-full-stack.sh
# Uses "test-model" - works with any backend
```

### Real Backend Testing

```bash
# Point to your real vLLM/Ollama/etc
export VLLM_BASE=http://your-server:8000
export GATEWAY_PORT=8080
export ALLOWED_API_KEYS=test-key

# Start gateway
npm start

# Test with YOUR model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "YOUR_MODEL_NAME",
    "stream": true,
    "messages": [{"role": "user", "content": "Test"}]
  }'
```

## Client Examples

### Python (OpenAI SDK)

```python
import openai

# Any model works - gateway just forwards it
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="your-api-key"
)

# Use any model name your backend supports
response = client.chat.completions.create(
    model="any-model-you-want",  # ← Gateway forwards as-is
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Node.js

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:8080/v1',
  apiKey: 'your-api-key',
});

// Any model works
const response = await client.chat.completions.create({
  model: 'any-model-you-want',  // ← Gateway forwards as-is
  messages: [{ role: 'user', content: 'Hello' }],
});
```

### cURL

```bash
# Any model works
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "any-model-you-want",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Switching Backends

To switch from one LLM to another, **just change the environment variable**:

```bash
# vLLM
VLLM_BASE=http://vllm-server:8000 npm start

# Ollama
VLLM_BASE=http://localhost:11434 npm start

# OpenAI
VLLM_BASE=https://api.openai.com npm start

# LocalAI
VLLM_BASE=http://localhost:8080 npm start

# Your custom server
VLLM_BASE=http://my-llm-server:9000 npm start
```

**No code changes needed!** ✅

## Model List Endpoint

The gateway forwards `/v1/models` to your backend:

```bash
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer your-key"
```

Returns whatever models your backend provides.

## Benefits of Model-Agnostic Design

### 1. Flexibility
- Switch models without changing gateway
- Use multiple models simultaneously
- Test different backends easily

### 2. Simplicity
- No model configuration in gateway
- No model validation logic
- Less code = fewer bugs

### 3. Future-Proof
- New models work automatically
- No updates needed for new LLMs
- Compatible with future APIs

### 4. Multi-Provider
- One gateway for all providers
- Consistent API for clients
- Easy A/B testing between models

## Common Patterns

### Pattern 1: Single Backend, Multiple Models

```bash
# One vLLM server with multiple models loaded
VLLM_BASE=http://vllm-server:8000 npm start

# Clients choose which model
curl ... -d '{"model": "llama-3.1", ...}'
curl ... -d '{"model": "qwen-2.5", ...}'
```

### Pattern 2: Multiple Backends, One Gateway Each

```bash
# Gateway for Qwen (port 8080)
GATEWAY_PORT=8080 VLLM_BASE=http://qwen-server:8000 npm start

# Gateway for Llama (port 8081)
GATEWAY_PORT=8081 VLLM_BASE=http://llama-server:8000 npm start

# Clients choose which gateway
```

### Pattern 3: Load Balancer + Multiple Gateways

```yaml
# docker-compose.yml
services:
  gateway-1:
    image: llm-gateway
    environment:
      VLLM_BASE: http://vllm-1:8000
  
  gateway-2:
    image: llm-gateway
    environment:
      VLLM_BASE: http://vllm-2:8000
  
  load-balancer:
    image: nginx
    # Routes to gateway-1, gateway-2
```

### Pattern 4: Intelligent Router

```typescript
// Custom router in front of gateway
app.post('/v1/chat/completions', async (req, res) => {
  const model = req.body.model;
  
  // Route based on model
  let gatewayUrl;
  if (model.includes('qwen')) {
    gatewayUrl = 'http://gateway-qwen:8080';
  } else if (model.includes('llama')) {
    gatewayUrl = 'http://gateway-llama:8080';
  } else {
    gatewayUrl = 'http://gateway-default:8080';
  }
  
  // Forward to appropriate gateway
  const response = await fetch(`${gatewayUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: req.headers,
    body: JSON.stringify(req.body)
  });
  
  res.send(await response.text());
});
```

## Verification

### Verify Gateway is Model-Agnostic

```bash
# Test with random model name
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "this-model-does-not-exist-but-gateway-forwards-it-anyway",
    "messages": [{"role": "user", "content": "Test"}]
  }'

# Gateway will forward it
# Backend will respond (error or success depends on backend)
```

### Check Gateway Logs

Gateway logs show it forwards without caring about model:

```
[Gateway] POST /v1/chat/completions
[Gateway] Forwarding to: http://backend:8000/v1/chat/completions
[Gateway] Model: any-model-name (forwarded as-is)
```

## Summary

✅ **Gateway is 100% model-agnostic**
- Never validates model names
- Never modifies model names
- Never hardcodes model names
- Simply forwards everything to backend

✅ **Works with any LLM backend**
- vLLM, Ollama, TGI, llama.cpp, etc.
- Any OpenAI-compatible API
- Your custom LLM server

✅ **No configuration needed**
- Just set `VLLM_BASE` to your backend
- Use any model your backend supports
- Switch backends anytime by changing env var

✅ **Client flexibility**
- Clients choose which model
- Gateway doesn't interfere
- Works exactly like direct API access

---

**The gateway's job:** Authenticate requests and forward them. That's it!  
**Not the gateway's job:** Know anything about models. 🚫

Use it with **any** LLM! 🚀

