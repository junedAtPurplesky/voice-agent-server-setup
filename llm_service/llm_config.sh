#!/usr/bin/env bash
# ==========================================================
# LLM Service Configuration
# ==========================================================
# Edit the values below to configure your LLM deployment
# Only uncommented settings will be used

# -------------------------------
# ACTIVE CONFIGURATION
# -------------------------------

# Model Settings
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct-AWQ"
HOST="0.0.0.0"
PORT="8000"

# Performance Settings
QUANTIZATION="awq"

# ==========================================================
# 🔧 Optimized Additions for Low VRAM + High Performance
# ==========================================================

# Memory & Performance
GPU_MEMORY_UTILIZATION="0.55"          # keep VRAM under control (safe range: 0.55–0.65)
TENSOR_PARALLEL_SIZE="1"               # single GPU
MAX_NUM_SEQS="4"                       # small batch for efficient GPU utilization
SWAP_SPACE="2"                         # 2GiB CPU swap backup to avoid OOM

# Stability & Runtime
ENFORCE_EAGER="--enforce-eager"        # prevent CUDA graph spikes
DISABLE_LOG_STATS="--disable-log-stats"  # reduce logging overhead

# Throughput Optimization
ENABLE_CHUNKED_PREFILL="--enable-chunked-prefill"  # stream long inputs efficiently
ENABLE_PREFIX_CACHING="--enable-prefix-caching"    # reuse cached prompt parts

# Model Precision (recommended for smaller VRAM GPUs)
DTYPE="bfloat16"                       # lighter than FP16, safer numerically
MAX_MODEL_LEN="2048"                   # limit context to save memory
MAX_NUM_BATCHED_TOKENS="1024"          # limit per-batch token load

# Tool / Function Calling
ENABLE_AUTO_TOOL_CHOICE="--enable-auto-tool-choice"
TOOL_CALL_PARSER="hermes"

# Advanced Tweaks
#EXTRA_FLAGS="--gpu-memory-utilization 0.55 --max-num-seqs 4 --max-num-batched-tokens 1024"

# ==========================================================
# ALL SUPPORTED FLAGS (Reference)
# ==========================================================
# (Everything below remains unchanged — reference only)

# Model Configuration
# MODEL_NAME="meta-llama/Llama-2-7b-chat-hf"
# TOKENIZER=""                           # Tokenizer name/path (default: same as model)
# TOKENIZER_MODE="auto"                  # Tokenizer mode: auto, slow
# TRUST_REMOTE_CODE=""                   # --trust-remote-code
# DOWNLOAD_DIR=""                        # Directory to download/load weights
# LOAD_FORMAT="auto"                     # Model weights format: auto, pt, safetensors, npcache, dummy
# DTYPE="auto"                           # Data type: auto, half, float16, bfloat16, float, float32
# KV_CACHE_DTYPE="auto"                  # Data type for kv cache storage
# MAX_MODEL_LEN=""                       # Model context length (default: from model config)
# REVISION=""                            # Model revision/branch
# CODE_REVISION=""                       # Code revision for remote code
# TOKENIZER_REVISION=""                  # Tokenizer revision

## Quantization
# QUANTIZATION="awq"                     # Quantization method: awq, gptq, squeezellm, fp8, etc.
# QUANTIZATION_PARAM_PATH=""             # Path to quantization params JSON

## Server Configuration
# HOST="0.0.0.0"                         # Host to bind server
# PORT="8000"                            # Port number
# UVL_LOG_LEVEL="info"                   # Logging level: debug, info, warning, error, critical
# API_KEY=""                             # API key for authentication
# SERVED_MODEL_NAME=""                   # Model name used in API (default: model path)
# CHAT_TEMPLATE=""                       # Chat template file path
# RESPONSE_ROLE="assistant"              # Role name for response
# SSL_KEYFILE=""                         # SSL key file path
# SSL_CERTFILE=""                        # SSL certificate file path
# SSL_CA_CERTS=""                        # SSL CA certificates file path
# SSL_CERT_REQS="0"                      # SSL cert requirements: 0=none, 1=optional, 2=required
# ROOT_PATH=""                           # FastAPI root_path for proxies
# MIDDLEWARE=""                          # Additional middleware modules

## Memory and Performance
# GPU_MEMORY_UTILIZATION="0.90"          # GPU memory utilization (0.0-1.0)
# MAX_NUM_SEQS="256"                     # Max number of sequences per iteration
# MAX_NUM_BATCHED_TOKENS=""              # Max tokens to be processed in a single batch
# MAX_PADDINGS="256"                     # Max number of paddings in a batch
# BLOCK_SIZE="16"                        # Token block size
# SWAP_SPACE="4"                         # CPU swap space size in GiB
# ENABLE_PREFIX_CACHING=""               # --enable-prefix-caching (automatic prefix caching)
# DISABLE_SLIDING_WINDOW=""              # --disable-sliding-window
# MAX_CONTEXT_LEN_TO_CAPTURE=""          # Max context len for CUDA graphs
# MAX_SEQ_LEN_TO_CAPTURE="8192"          # Max seq len for CUDA graphs

## Parallelism
# TENSOR_PARALLEL_SIZE="1"               # Number of tensor parallel replicas
# PIPELINE_PARALLEL_SIZE="1"             # Number of pipeline parallel stages
# DISTRIBUTED_EXECUTOR_BACKEND=""        # Backend for distributed serving: ray, mp

## Scheduling
# SCHEDULER_DELAY_FACTOR="0.0"           # Delay factor for scheduling (0.0=no delay)
# ENABLE_CHUNKED_PREFILL=""              # --enable-chunked-prefill (experimental)
# MAX_NUM_ON_THE_FLY=""                  # Max number of on-the-fly requests
# SPECULATIVE_MODEL=""                   # Speculative decoding model name
# NUM_SPECULATIVE_TOKENS=""              # Number of speculative tokens
# SPECULATIVE_MAX_MODEL_LEN=""           # Max model length for spec decoding

## Engine Options
# DISABLE_LOG_STATS=""                   # --disable-log-stats (disable logging statistics)
# ENFORCE_EAGER=""                       # --enforce-eager (disable CUDA graph)
# DISABLE_CUSTOM_ALL_REDUCE=""           # --disable-custom-all-reduce
# ENABLE_LORA=""                         # --enable-lora (enable LoRA adapters)
# MAX_LORAS="1"                          # Max number of LoRA adapters
# MAX_LORA_RANK="16"                     # Max LoRA rank
# LORA_MODULES=""                        # LoRA module configurations
# FULLY_SHARDED_LORAS=""                 # --fully-sharded-loras

## Device Configuration
# DEVICE="auto"                          # Device type: auto, cuda, cpu, openvino, tpu, xpu
# NUM_SCHEDULER_STEPS="1"                # Number of scheduler steps
# MULTI_STEP_STREAM_OUTPUTS=""           # --multi-step-stream-outputs

## Vision/Multimodal
# IMAGE_INPUT_TYPE="pixel_values"        # Image input type for vision models
# IMAGE_TOKEN_ID=""                      # Image token ID
# IMAGE_INPUT_SHAPE=""                   # Image input shape (e.g., 1,3,224,224)
# IMAGE_FEATURE_SIZE=""                  # Image feature size
# LIMIT_MM_PER_PROMPT=""                 # Limit multimodal items per prompt

## Tool/Function Calling
ENABLE_AUTO_TOOL_CHOICE="--enable-auto-tool-choice"  # Enable auto tool choice
TOOL_CALL_PARSER="hermes"                            # Tool call parser: hermes, etc.

## Guided Decoding
# GUIDED_DECODING_BACKEND="outlines"     # Backend for guided decoding: outlines, lm-format-enforcer

## Logging and Monitoring
# DISABLE_LOG_REQUESTS=""                # --disable-log-requests
# MAX_LOG_LEN=""                         # Max length of log messages

## OpenAI Compatibility
# DISABLE_FRONTEND_MULTIPROCESSING=""    # --disable-frontend-multiprocessing

## Additional Custom Flags
#EXTRA_FLAGS="--gpu-memory-utilization 0.55 --max-num-seqs 4 --max-num-batched-tokens 1024"

# ==========================================================
# Example Configurations for Different Models
# ==========================================================
