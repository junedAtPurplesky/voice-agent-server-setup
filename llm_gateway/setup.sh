#!/usr/bin/env bash
set -e

# ==============================
# Dynamic Path Configuration
# ==============================
CURRENT_DIR="$(pwd)"
PYTHON_VERSION="python3"
VENV_PATH="${CURRENT_DIR}/.venv"

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

echo "[5/5] Setup complete!"
echo "Use './manage.sh start' to run the gateway in background using nohup."
