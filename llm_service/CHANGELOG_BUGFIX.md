# Changelog - Model Name Bug Fix

## Version 1.1.0 - Model Name Auto-Detection

### Bug Fixed
- ❌ **Old behavior**: Used `"model": "default"` which doesn't work with vLLM
- ✅ **New behavior**: Auto-detects actual model name from `/v1/models` endpoint

### Changes

#### 1. Python Test Clients Updated
All Python test files now support auto-detection and manual specification:

**test_client.py**
- Added `model` parameter to constructor
- Auto-detects model in `test_health()` method
- Uses real model name in all API calls
- Added `--model` CLI argument
- Added system message to chat completions

**test_stream.py**
- Added `model` parameter to constructor
- Added `get_model_name()` helper method
- Uses real model name in streaming requests
- Added system message to chat completions
- Added `--model` CLI argument

**load_test.py**
- Added `model` parameter to constructor
- Added `get_model_name()` helper method
- Uses real model name in load test requests
- Added `--model` CLI argument

#### 2. Shell Script Updated
**test_llm.sh**
- Auto-detects model using `jq` to parse `/v1/models` response
- Uses detected model in all curl requests
- Added system message to chat completions
- Shows detected model in test output

### Usage

#### Auto-Detection (Default)
```bash
# Model automatically detected - just run the tests!
python3 test_client.py
python3 test_stream.py
python3 load_test.py
./test_llm.sh quick
```

#### Manual Specification
```bash
# Explicitly specify model if needed
python3 test_client.py --model "Qwen/Qwen2.5-0.5B-Instruct-AWQ"
python3 test_stream.py --model "meta-llama/Meta-Llama-3-8B"
python3 load_test.py --model "mistralai/Mistral-7B-Instruct"
```

### Example Output
```bash
$ python3 test_client.py

🏥 Testing Service Health...
✅ Service is healthy (Response time: 0.145s)
📋 Available models: {
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
      "object": "model",
      ...
    }
  ]
}
🎯 Using model: Qwen/Qwen2.5-0.5B-Instruct-AWQ

1️⃣  Testing Basic Completion...
✅ Completion test passed (1.234s, 47 tokens)
...
```

### Breaking Changes
None! The changes are backward compatible:
- If model detection fails, falls back to "model"
- All existing command-line arguments still work
- Auto-detection is automatic and transparent

### Migration Guide
No migration needed! Just update and run:
```bash
# Old way (still works)
python3 test_client.py

# New way (also works)
python3 test_client.py --model "your-model-name"
```

### Files Modified
- ✅ test_client.py (added model auto-detection)
- ✅ test_stream.py (added model auto-detection)
- ✅ load_test.py (added model auto-detection)
- ✅ test_llm.sh (added model auto-detection)
- ✅ .gitignore (added .test_*.sh pattern)

### Files Added
- ✅ BUGFIX_MODEL_NAMES.md (detailed bug fix documentation)
- ✅ CHANGELOG_BUGFIX.md (this file)
- ✅ .test_model_detection.sh (test script for manual verification)

### Testing
To verify the fix works:
```bash
# Quick test
python3 test_client.py

# Or use the test script
./.test_model_detection.sh
```

### Credits
Bug reported and working example provided by user. Thank you! 🙏

---

**Version**: 1.1.0  
**Date**: November 5, 2025  
**Status**: ✅ Fixed and Tested
