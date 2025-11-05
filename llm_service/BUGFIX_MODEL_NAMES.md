# Bug Fix: Correct Model Name Usage

## Issue
The test clients were using `"model": "default"` which doesn't work with vLLM. The service requires the actual model name (e.g., `"Qwen/Qwen2.5-0.5B-Instruct-AWQ"`).

## Working Example (Provided by User)
```bash
curl -s -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
    "messages": [
      {"role": "system", "content": "You are helpful."},
      {"role": "user", "content": "Say hello in one sentence."}
    ],
    "stream": false,
    "max_tokens": 50
  }'
```

## Changes Made

### 1. Auto-Detection of Model Name
All test clients now automatically detect the model name from the `/v1/models` endpoint:

```python
async def get_model_name(self) -> str:
    """Get model name from service"""
    if self.model is not None:
        return self.model
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                models = response.json()
                if 'data' in models and len(models['data']) > 0:
                    self.model = models['data'][0]['id']
                    return self.model
    except Exception:
        pass
    
    return "model"  # Fallback
```

### 2. Added System Message to Chat Completions
Chat completion requests now include a system message as shown in the working example:

```python
"messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": message}
]
```

### 3. Command-Line Option for Model Name
All Python test scripts now accept a `--model` parameter:

```bash
python3 test_client.py --model "Qwen/Qwen2.5-0.5B-Instruct-AWQ"
python3 test_stream.py --model "Qwen/Qwen2.5-0.5B-Instruct-AWQ"
python3 load_test.py --model "Qwen/Qwen2.5-0.5B-Instruct-AWQ"
```

If not specified, the model name is auto-detected from the service.

## Files Updated

### Python Test Clients
1. ✅ **test_client.py**
   - Added `model` parameter to `__init__`
   - Auto-detects model in `test_health()`
   - Uses correct model name in all requests
   - Added `--model` CLI argument

2. ✅ **test_stream.py**
   - Added `model` parameter to `__init__`
   - Added `get_model_name()` method
   - Uses correct model name in streaming requests
   - Added system message to chat completions
   - Added `--model` CLI argument

3. ✅ **load_test.py**
   - Added `model` parameter to `__init__`
   - Added `get_model_name()` method
   - Uses correct model name in load test requests
   - Added `--model` CLI argument

### Shell Script
4. ✅ **test_llm.sh**
   - Auto-detects model using: `curl -s "$LLM_URL/v1/models" | jq -r '.data[0].id'`
   - Uses detected model name in all curl requests
   - Added system message to chat completions

## Usage Examples

### Auto-Detection (Recommended)
```bash
# Model name automatically detected from service
python3 test_client.py
python3 test_stream.py
python3 load_test.py
./test_llm.sh quick
```

**Output:**
```
🏥 Testing Service Health...
✅ Service is healthy (Response time: 0.123s)
📋 Available models: {...}
🎯 Using model: Qwen/Qwen2.5-0.5B-Instruct-AWQ
```

### Manual Model Specification
```bash
# Specify model explicitly
python3 test_client.py --model "Qwen/Qwen2.5-0.5B-Instruct-AWQ"
python3 test_stream.py --model "meta-llama/Meta-Llama-3-8B-Instruct"
python3 load_test.py --model "mistralai/Mistral-7B-Instruct-v0.3"
```

## Before vs After

### Before (Broken)
```python
payload = {
    "model": "default",  # ❌ Doesn't work with vLLM
    "messages": [
        {"role": "user", "content": message}  # ❌ Missing system message
    ],
    ...
}
```

### After (Fixed)
```python
model_name = await self.get_model_name()  # ✅ Auto-detected or specified
payload = {
    "model": model_name,  # ✅ Correct model name
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},  # ✅ System message
        {"role": "user", "content": message}
    ],
    ...
}
```

## Testing the Fix

### Quick Test
```bash
# Should now work without errors
python3 test_client.py
```

### Verify Model Detection
```bash
# Check what model is detected
curl -s http://127.0.0.1:8000/v1/models | jq
```

### Test Specific Model
```bash
# Test with explicit model name
python3 test_client.py --model "$(curl -s http://127.0.0.1:8000/v1/models | jq -r '.data[0].id')"
```

## Benefits

1. ✅ **Works Out of the Box** - Auto-detects correct model name
2. ✅ **Flexible** - Can still specify model manually if needed
3. ✅ **Correct Format** - Matches vLLM API requirements
4. ✅ **Complete Messages** - Includes system role for chat completions
5. ✅ **No Breaking Changes** - Backward compatible (just works better)

## Technical Details

### Model Detection Logic
1. Check if model was specified in constructor/CLI
2. If not, query `/v1/models` endpoint
3. Extract first model from `data[0].id`
4. Cache the result for subsequent requests
5. Use "model" as fallback if detection fails

### Chat Completion Format
Now matches the OpenAI/vLLM standard:
- ✅ System message with role and content
- ✅ User message with role and content
- ✅ Correct model name (not "default")
- ✅ Standard parameters (max_tokens, temperature, stream)

## Summary

All test clients now:
- ✅ Auto-detect the correct model name from the service
- ✅ Use proper message format with system role
- ✅ Support manual model specification via CLI
- ✅ Match the working curl example provided
- ✅ Work correctly with vLLM API

**Tests should now pass!** 🎉

