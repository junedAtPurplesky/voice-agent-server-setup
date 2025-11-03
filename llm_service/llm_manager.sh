#!/usr/bin/env bash
# ==========================================================
# LLM Service Manager - v1.0
# Author: Moin Baig
# Description: Manage VLLM model lifecycle (install, start, stop, logs, etc.)
# ==========================================================

set -e

# -------------------------------
# Configuration (Editable Section)
# -------------------------------
MODEL_NAME="Qwen/Qwen2.5-0.5B-Instruct-AWQ"
HOST="0.0.0.0"
PORT="8000"
QUANTIZATION="awq"
GPU_MEMORY_UTILIZATION="0.6"
TENSOR_PARALLEL_SIZE="1"
MAX_NUM_SEQS="1"
SWAP_SPACE="1"
ENFORCE_EAGER="--enforce-eager"
DISABLE_LOG_STATS="--disable-log-stats"

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
  cd "$WORKDIR"
  source "$VENV_DIR/bin/activate"

  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "⚠️ LLM already running with PID $(cat "$PIDFILE"). Stop it first."
    exit 1
  fi

  CMD="vllm serve $MODEL_NAME \
    --host $HOST \
    --port $PORT \
    --quantization $QUANTIZATION \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    --tensor-parallel-size $TENSOR_PARALLEL_SIZE \
    --max-num-seqs $MAX_NUM_SEQS \
    --swap-space $SWAP_SPACE \
    $ENFORCE_EAGER \
    $DISABLE_LOG_STATS"

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
