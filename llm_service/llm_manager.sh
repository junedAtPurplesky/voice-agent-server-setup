#!/usr/bin/env bash
# ==========================================================
# LLM Service Manager - v1.1
# Author: Moin Baig
# Description: Manage VLLM model lifecycle (install, start, stop, logs, etc.)
# ==========================================================

set -e

# -------------------------------
# Configuration Loading
# -------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/llm_config.sh"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
  source "$CONFIG_FILE"
else
  echo "❌ Error: Configuration file not found: $CONFIG_FILE"
  echo "Please create llm_config.sh in the same directory as this script."
  exit 1
fi

# Paths
WORKDIR="$HOME/llm_service"
VENV_DIR="$WORKDIR/.venv"
LOGFILE="$WORKDIR/llm_service.log"
PIDFILE="$WORKDIR/llm_service.pid"

# -------------------------------
# Helper Functions
# -------------------------------

install_deps() {
  echo "📦 Installing system dependencies..."
  sudo apt update
  sudo apt install -y build-essential git wget curl unzip python3-venv python3-dev cmake libomp-dev
}

setup_env() {
  echo "🧰 Setting up Python virtual environment..."
  mkdir -p "$WORKDIR"
  cd "$WORKDIR"

  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  source "$VENV_DIR/bin/activate"

  echo "⬆️ Upgrading pip and installing Python dependencies..."
  pip install --upgrade pip setuptools wheel
  pip install "vllm" "fastapi" "uvicorn[standard]" "httpx[http2]" "python-multipart" "python-dotenv" hf_transfer
}

start_llm() {
  echo "🚀 Starting LLM Service..."
  echo "Model: $MODEL_NAME"
  echo "Port: $PORT"
  
  cd "$WORKDIR"
  source "$VENV_DIR/bin/activate"

  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "⚠️ LLM already running with PID $(cat "$PIDFILE"). Stop it first."
    exit 1
  fi

  # Build command dynamically
  CMD="vllm serve $MODEL_NAME"
  
  # Add configured flags (only if set)
  [ -n "$HOST" ] && CMD="$CMD --host $HOST"
  [ -n "$PORT" ] && CMD="$CMD --port $PORT"
  [ -n "$QUANTIZATION" ] && CMD="$CMD --quantization $QUANTIZATION"
  [ -n "$GPU_MEMORY_UTILIZATION" ] && CMD="$CMD --gpu-memory-utilization $GPU_MEMORY_UTILIZATION"
  [ -n "$TENSOR_PARALLEL_SIZE" ] && CMD="$CMD --tensor-parallel-size $TENSOR_PARALLEL_SIZE"
  [ -n "$MAX_NUM_SEQS" ] && CMD="$CMD --max-num-seqs $MAX_NUM_SEQS"
  [ -n "$SWAP_SPACE" ] && CMD="$CMD --swap-space $SWAP_SPACE"
  [ -n "$TOKENIZER" ] && CMD="$CMD --tokenizer $TOKENIZER"
  [ -n "$TOKENIZER_MODE" ] && CMD="$CMD --tokenizer-mode $TOKENIZER_MODE"
  [ -n "$DOWNLOAD_DIR" ] && CMD="$CMD --download-dir $DOWNLOAD_DIR"
  [ -n "$LOAD_FORMAT" ] && CMD="$CMD --load-format $LOAD_FORMAT"
  [ -n "$DTYPE" ] && CMD="$CMD --dtype $DTYPE"
  [ -n "$KV_CACHE_DTYPE" ] && CMD="$CMD --kv-cache-dtype $KV_CACHE_DTYPE"
  [ -n "$MAX_MODEL_LEN" ] && CMD="$CMD --max-model-len $MAX_MODEL_LEN"
  [ -n "$REVISION" ] && CMD="$CMD --revision $REVISION"
  [ -n "$CODE_REVISION" ] && CMD="$CMD --code-revision $CODE_REVISION"
  [ -n "$TOKENIZER_REVISION" ] && CMD="$CMD --tokenizer-revision $TOKENIZER_REVISION"
  [ -n "$QUANTIZATION_PARAM_PATH" ] && CMD="$CMD --quantization-param-path $QUANTIZATION_PARAM_PATH"
  [ -n "$BLOCK_SIZE" ] && CMD="$CMD --block-size $BLOCK_SIZE"
  [ -n "$PIPELINE_PARALLEL_SIZE" ] && CMD="$CMD --pipeline-parallel-size $PIPELINE_PARALLEL_SIZE"
  [ -n "$DEVICE" ] && CMD="$CMD --device $DEVICE"
  
  # Boolean/flag-only options
  [ -n "$TRUST_REMOTE_CODE" ] && CMD="$CMD $TRUST_REMOTE_CODE"
  [ -n "$ENFORCE_EAGER" ] && CMD="$CMD $ENFORCE_EAGER"
  [ -n "$DISABLE_LOG_STATS" ] && CMD="$CMD $DISABLE_LOG_STATS"
  [ -n "$DISABLE_CUSTOM_ALL_REDUCE" ] && CMD="$CMD $DISABLE_CUSTOM_ALL_REDUCE"
  [ -n "$ENABLE_PREFIX_CACHING" ] && CMD="$CMD $ENABLE_PREFIX_CACHING"
  [ -n "$DISABLE_SLIDING_WINDOW" ] && CMD="$CMD $DISABLE_SLIDING_WINDOW"
  [ -n "$ENABLE_LORA" ] && CMD="$CMD $ENABLE_LORA"
  [ -n "$ENABLE_CHUNKED_PREFILL" ] && CMD="$CMD $ENABLE_CHUNKED_PREFILL"
  
  # Tool/Function calling
  [ -n "$ENABLE_AUTO_TOOL_CHOICE" ] && CMD="$CMD $ENABLE_AUTO_TOOL_CHOICE"
  [ -n "$TOOL_CALL_PARSER" ] && CMD="$CMD --tool-call-parser $TOOL_CALL_PARSER"
  
  # Add extra custom flags
  [ -n "$EXTRA_FLAGS" ] && CMD="$CMD $EXTRA_FLAGS"

  echo "Running command: $CMD"
  nohup bash -c "$CMD" > "$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  echo "✅ LLM started (PID $(cat "$PIDFILE"))"
}

stop_llm() {
  if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
      echo "🛑 Stopping LLM (PID $PID)..."
      kill "$PID"
      rm -f "$PIDFILE"
      echo "✅ LLM stopped."
    else
      echo "⚠️ Process not running. Removing stale PID file."
      rm -f "$PIDFILE"
    fi
  else
    echo "⚠️ No PID file found. LLM may not be running."
  fi
}

status_llm() {
  if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
      echo "✅ LLM is running (PID $PID)"
    else
      echo "⚠️ LLM PID file exists but process not running."
    fi
  else
    echo "❌ LLM not running."
  fi
}

logs_llm() {
  echo "📜 Showing logs (Ctrl+C to exit)..."
  tail -f "$LOGFILE"
}

test_llm() {
  echo "🧪 Testing LLM Performance..."
  source "$VENV_DIR/bin/activate"

  # Simple health test
  echo "Checking LLM health..."
  curl -s "http://127.0.0.1:$PORT/v1/models" | jq || echo "⚠️ Health check failed."

  # Basic load test using ApacheBench
  if ! command -v ab &> /dev/null; then
    echo "Installing ApacheBench (apache2-utils)..."
    sudo apt install -y apache2-utils
  fi

  echo "Running basic performance test (5 requests, concurrency 1)..."
  ab -n 5 -c 1 "http://127.0.0.1:$PORT/v1/completions" || echo "⚠️ Test request failed."
}

restart_llm() {
  stop_llm
  sleep 2
  start_llm
}

# -------------------------------
# Command Dispatcher
# -------------------------------
case "$1" in
  install)
    install_deps
    ;;
  setup)
    setup_env
    ;;
  start)
    start_llm
    ;;
  stop)
    stop_llm
    ;;
  restart)
    restart_llm
    ;;
  status)
    status_llm
    ;;
  logs)
    logs_llm
    ;;
  test)
    test_llm
    ;;
  *)
    echo "Usage: $0 {install|setup|start|stop|restart|status|logs|test}"
    ;;
esac
