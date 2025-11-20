#!/bin/bash

# Stop on error
set -e

echo "--- Starting Generic vLLM Deployment ---"

# 1. Environment Setup & Defaults

# Core Model Settings
MODEL_NAME=${MODEL_NAME:-"Qwen/Qwen2.5-7B-Instruct-AWQ"}
CACHE_DIR=${HF_HOME:-"/runpod-volume/huggingface_cache"}
PORT=${PORT:-8000}
API_KEY=${API_KEY:-"default-key"}

# vLLM Configuration
MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
GPU_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.95}
DTYPE=${DTYPE:-"auto"}
QUANTIZATION=${QUANTIZATION:-""} # Empty means no quantization or auto-detect
TRUST_REMOTE_CODE=${TRUST_REMOTE_CODE:-"true"}
ENABLE_AUTO_TOOL_CHOICE=${ENABLE_AUTO_TOOL_CHOICE:-"true"}
TOOL_CALL_PARSER=${TOOL_CALL_PARSER:-"hermes"}

# Enable hf_transfer for faster downloads
export HF_HUB_ENABLE_HF_TRANSFER=1

# Create cache directory
mkdir -p "$CACHE_DIR"

echo "--- Configuration ---"
echo "Model: $MODEL_NAME"
echo "Cache Dir: $CACHE_DIR"
echo "Port: $PORT"
echo "Max Context: $MAX_MODEL_LEN"
echo "GPU Util: $GPU_UTILIZATION"
echo "Quantization: ${QUANTIZATION:-'None/Auto'}"

# 2. Model Download Check
if [ -n "$HUGGING_FACE_HUB_TOKEN" ]; then
    echo "Logging in to Hugging Face..."
    huggingface-cli login --token "$HUGGING_FACE_HUB_TOKEN"
fi

echo "Checking model availability..."
# Downloads only if not cached
huggingface-cli download "$MODEL_NAME" --cache-dir "$CACHE_DIR"

# 3. Construct vLLM Command
# Start with the base command and core arguments
CMD="python3 -m vllm.entrypoints.openai.api_server \
    --model \"$MODEL_NAME\" \
    --download-dir \"$CACHE_DIR\" \
    --host 0.0.0.0 \
    --port \"$PORT\" \
    --gpu-memory-utilization \"$GPU_UTILIZATION\" \
    --max-model-len \"$MAX_MODEL_LEN\" \
    --dtype \"$DTYPE\" \
    --api-key \"$API_KEY\""

# --- Explicit Configuration Flags ---

# Quantization
if [ -n "$QUANTIZATION" ]; then CMD="$CMD --quantization \"$QUANTIZATION\""; fi
if [ -n "$KV_CACHE_DTYPE" ]; then CMD="$CMD --kv-cache-dtype \"$KV_CACHE_DTYPE\""; fi

# Distributed Inference
if [ -n "$TENSOR_PARALLEL_SIZE" ]; then CMD="$CMD --tensor-parallel-size \"$TENSOR_PARALLEL_SIZE\""; fi
if [ -n "$PIPELINE_PARALLEL_SIZE" ]; then CMD="$CMD --pipeline-parallel-size \"$PIPELINE_PARALLEL_SIZE\""; fi

# LoRA Adapters
if [ "$ENABLE_LORA" = "true" ]; then CMD="$CMD --enable-lora"; fi
if [ -n "$MAX_LORAS" ]; then CMD="$CMD --max-loras \"$MAX_LORAS\""; fi
if [ -n "$MAX_LORA_RANK" ]; then CMD="$CMD --max-lora-rank \"$MAX_LORA_RANK\""; fi
if [ -n "$LORA_MODULES" ]; then CMD="$CMD --lora-modules $LORA_MODULES"; fi

# Model & Tokenizer
if [ "$TRUST_REMOTE_CODE" = "true" ]; then CMD="$CMD --trust-remote-code"; fi
if [ -n "$TOKENIZER" ]; then CMD="$CMD --tokenizer \"$TOKENIZER\""; fi
if [ -n "$TOKENIZER_MODE" ]; then CMD="$CMD --tokenizer-mode \"$TOKENIZER_MODE\""; fi
if [ -n "$REVISION" ]; then CMD="$CMD --revision \"$REVISION\""; fi
if [ -n "$TOKENIZER_REVISION" ]; then CMD="$CMD --tokenizer-revision \"$TOKENIZER_REVISION\""; fi

# Scheduling & Memory
if [ -n "$MAX_NUM_SEQS" ]; then CMD="$CMD --max-num-seqs \"$MAX_NUM_SEQS\""; fi
if [ -n "$MAX_NUM_BATCHED_TOKENS" ]; then CMD="$CMD --max-num-batched-tokens \"$MAX_NUM_BATCHED_TOKENS\""; fi
if [ -n "$SWAP_SPACE" ]; then CMD="$CMD --swap-space \"$SWAP_SPACE\""; fi
if [ "$ENFORCE_EAGER" = "true" ]; then CMD="$CMD --enforce-eager"; fi

# Server & API
if [ -n "$SERVED_MODEL_NAME" ]; then CMD="$CMD --served-model-name \"$SERVED_MODEL_NAME\""; fi
if [ -n "$CHAT_TEMPLATE" ]; then CMD="$CMD --chat-template \"$CHAT_TEMPLATE\""; fi
if [ -n "$UV_LOOP" ]; then CMD="$CMD --uv-loop \"$UV_LOOP\""; fi
if [ -n "$LOG_LEVEL" ]; then CMD="$CMD --log-level \"$LOG_LEVEL\""; fi

# Tool Use
if [ "$ENABLE_AUTO_TOOL_CHOICE" = "true" ]; then CMD="$CMD --enable-auto-tool-choice"; fi
if [ -n "$TOOL_CALL_PARSER" ]; then CMD="$CMD --tool-call-parser \"$TOOL_CALL_PARSER\""; fi

# Add any extra arguments passed via EXTRA_ARGS env var
if [ -n "$EXTRA_ARGS" ]; then
    echo "Adding extra arguments: $EXTRA_ARGS"
    CMD="$CMD $EXTRA_ARGS"
fi

# 4. Launch vLLM Server
echo "--- Launching vLLM Server ---"
echo "Command: $CMD"
eval exec $CMD