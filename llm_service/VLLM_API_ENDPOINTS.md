# vLLM API Endpoints Reference

This document confirms that our test clients use the correct vLLM OpenAI-compatible API endpoints.

## ✅ Verified vLLM Endpoints

### Currently Used (Correct)

#### 1. List Models
```
GET http://127.0.0.1:8000/v1/models
```
**Purpose**: List all available models  
**Used in**: All test clients for auto-detection  
**Response**: JSON with model information

**Example:**
```bash
curl http://127.0.0.1:8000/v1/models
```

#### 2. Text Completions
```
POST http://127.0.0.1:8000/v1/completions
```
**Purpose**: Generate text completions  
**Used in**: `test_client.py`, `test_stream.py`, `load_test.py`, `test_llm.sh`  
**Supports**: Streaming and non-streaming

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "prompt": "Hello, how are you?",
    "max_tokens": 50,
    "temperature": 0.7,
    "stream": false
  }'
```

#### 3. Chat Completions
```
POST http://127.0.0.1:8000/v1/chat/completions
```
**Purpose**: Chat-based completions with conversation context  
**Used in**: `test_client.py`, `test_stream.py`, `test_llm.sh`  
**Supports**: Streaming and non-streaming

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Say hello in one sentence."}
    ],
    "max_tokens": 50,
    "temperature": 0.7,
    "stream": false
  }'
```

### Additional vLLM Endpoints (Available)

#### 4. Health Check (Optional)
```
GET http://127.0.0.1:8000/health
```
**Purpose**: Simple health check endpoint  
**Alternative to**: `/v1/models` for health checking

**Example:**
```bash
curl http://127.0.0.1:8000/health
```

#### 5. Version Info (Optional)
```
GET http://127.0.0.1:8000/version
```
**Purpose**: Get vLLM version information

**Example:**
```bash
curl http://127.0.0.1:8000/version
```

#### 6. Embeddings (Optional)
```
POST http://127.0.0.1:8000/v1/embeddings
```
**Purpose**: Generate embeddings for text  
**Note**: Only available with embedding models

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-embedding-model",
    "input": "Text to embed"
  }'
```

## API Compatibility

### ✅ Supported by Our Test Clients

| Endpoint | Method | Purpose | Test Client Support |
|----------|--------|---------|-------------------|
| `/v1/models` | GET | List models | ✅ All clients |
| `/v1/completions` | POST | Text completion | ✅ All clients |
| `/v1/chat/completions` | POST | Chat completion | ✅ All clients |
| Streaming | POST | SSE streaming | ✅ test_stream.py, load_test.py |

### ⚠️ vLLM Unsupported Parameters

According to vLLM documentation, these OpenAI parameters are **NOT** supported:

**Chat Completions:**
- `tools` - Function calling not supported
- `tool_choice` - Function calling not supported

**Text Completions:**
- `suffix` - Not supported

**Our test clients don't use these**, so we're compatible! ✅

## Request Format

### Standard Parameters (All Supported)

```json
{
  "model": "string (required)",
  "prompt": "string (for completions)",
  "messages": "array (for chat)",
  "max_tokens": "integer",
  "temperature": "float (0.0-2.0)",
  "top_p": "float (0.0-1.0)",
  "n": "integer",
  "stream": "boolean",
  "stop": "string or array",
  "presence_penalty": "float",
  "frequency_penalty": "float",
  "logit_bias": "object",
  "user": "string"
}
```

### Streaming Response Format

When `stream: true`, vLLM returns Server-Sent Events (SSE):

```
data: {"id":"cmpl-xxx","object":"text_completion","created":xxx,"model":"xxx","choices":[{"text":"chunk","index":0,"logprobs":null,"finish_reason":null}]}

data: {"id":"cmpl-xxx","object":"text_completion","created":xxx,"model":"xxx","choices":[{"text":" text","index":0,"logprobs":null,"finish_reason":null}]}

data: [DONE]
```

**Our test clients handle this correctly!** ✅

## Verification

### Test All Endpoints

```bash
# 1. Test models endpoint
curl http://127.0.0.1:8000/v1/models | jq

# 2. Test health (optional)
curl http://127.0.0.1:8000/health

# 3. Test version (optional)
curl http://127.0.0.1:8000/version

# 4. Test completion
curl -X POST http://127.0.0.1:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "prompt": "Test",
    "max_tokens": 10
  }'

# 5. Test chat
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 10
  }'
```

## Implementation Status

### ✅ What We're Using (Correct)

1. **Base URL**: `http://127.0.0.1:8000` ✅
2. **Models Endpoint**: `/v1/models` ✅
3. **Completions**: `/v1/completions` ✅
4. **Chat Completions**: `/v1/chat/completions` ✅
5. **Model Name**: Auto-detected from `/v1/models` ✅
6. **Streaming**: SSE format with `data:` prefix ✅
7. **Message Format**: Proper role-based messages ✅

### ✨ Optional Enhancements

We could add (but not required):
- `/health` endpoint for simpler health checks
- `/version` endpoint for version tracking
- `/v1/embeddings` for embedding models

## Conclusion

**✅ Our test clients are using the correct vLLM API endpoints!**

All endpoints match vLLM's OpenAI-compatible API specification:
- Correct URLs
- Correct methods
- Correct request formats
- Correct response handling
- Proper streaming support

No changes needed - everything is already correctly implemented! 🎉

## References

- vLLM Documentation: https://docs.vllm.ai/
- OpenAI API Reference: https://platform.openai.com/docs/api-reference
- vLLM GitHub: https://github.com/vllm-project/vllm

---

**Version**: 1.2.0  
**Last Verified**: November 5, 2025  
**Status**: ✅ All endpoints verified and correct

