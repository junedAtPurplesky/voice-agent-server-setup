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
GPU_MEMORY_UTILIZATION="0.60"          # RTX 3090 (24GB) — safe to target ~0.55-0.65
TENSOR_PARALLEL_SIZE="1"
MAX_NUM_SEQS="4"
SWAP_SPACE="2"

# Stability & Runtime
ENFORCE_EAGER="--enforce-eager"
DISABLE_LOG_STATS="--disable-log-stats"

# Throughput Optimization
ENABLE_CHUNKED_PREFILL="--enable-chunked-prefill"
ENABLE_PREFIX_CACHING="--enable-prefix-caching"

# Model Precision (AWQ requires float16)
DTYPE="float16"                        # <-- FIX: float16 required for QUANTIZATION="awq"
MAX_MODEL_LEN="2048"
MAX_NUM_BATCHED_TOKENS="1024"

# Tool / Function Calling
ENABLE_AUTO_TOOL_CHOICE="--enable-auto-tool-choice"
TOOL_CALL_PARSER="hermes"

# Single EXTRA_FLAGS (keep only this one; remove any other EXTRA_FLAGS lower in file)
EXTRA_FLAGS="--gpu-memory-utilization 0.60 --max-num-seqs 4 --max-num-batched-tokens 1024 --dtype float16"