#!/usr/bin/env bash

# Dynamic current directory
CURRENT_DIR="$(pwd)"
VENV_PATH="${CURRENT_DIR}/.venv"
VLLM_BIN="${VENV_PATH}/bin/vllm"

# Model configuration
MODEL_NAME="Qwen/Qwen2.5-0.5B-Instruct-AWQ"
HOST="0.0.0.0"
PORT=8000

# vLLM Flags (editable)
VLLM_FLAGS=(
  "--quantization awq"
  "--gpu-memory-utilization 0.6"
  "--tensor-parallel-size 1"
  "--max-num-seqs 1"
  "--swap-space 1"
  "--enforce-eager"
  "--disable-log-stats"
)

# Final command (dynamic path)
VLLM_CMD="${VLLM_BIN} serve ${MODEL_NAME} \
  --host ${HOST} \
  --port ${PORT} \
  ${VLLM_FLAGS[@]}"
