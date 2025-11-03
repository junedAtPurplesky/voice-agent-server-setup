#!/usr/bin/env bash
set -e

# ==============================
# Dynamic Path Configuration
# ==============================
CURRENT_DIR="$(pwd)"
PYTHON_VERSION="python3"
VENV_PATH="${CURRENT_DIR}/.venv"
LOG_FILE="${CURRENT_DIR}/llm_service.log"
ERR_FILE="${CURRENT_DIR}/llm_service.err"

echo "[1/5] Updating system..."
sudo apt update -y && sudo apt install -y build-essential git wget curl unzip ${PYTHON_VERSION}-venv ${PYTHON_VERSION}-dev cmake libomp-dev

echo "[2/5] Creating virtual environment in current directory..."
if [ ! -d "${VENV_PATH}" ]; then
  ${PYTHON_VERSION} -m venv "${VENV_PATH}"
fi
source "${VENV_PATH}/bin/activate"

echo "[3/5] Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

echo "[4/5] Installing Python dependencies..."
if [ -f "${CURRENT_DIR}/requirements.txt" ]; then
  pip install -r "${CURRENT_DIR}/requirements.txt"
else
  echo "❌ requirements.txt not found in ${CURRENT_DIR}"
  exit 1
fi

echo "[5/5] Starting LLM service in detached mode..."
if [ -f "${CURRENT_DIR}/vllm_config.sh" ]; then
  source "${CURRENT_DIR}/vllm_config.sh"
  nohup bash -c "eval \"$VLLM_CMD\"" > "$LOG_FILE" 2> "$ERR_FILE" &
  echo "✅ LLM service started in background (PID: $!)."
  echo "   Logs: $LOG_FILE"
  echo "   Errors: $ERR_FILE"
else
  echo "❌ vllm_config.sh not found in ${CURRENT_DIR}"
  exit 1
fi

echo "✅ Setup complete!"
