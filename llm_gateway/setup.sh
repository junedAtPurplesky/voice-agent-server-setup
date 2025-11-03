#!/usr/bin/env bash
set -e

# ==============================
# Dynamic Path Configuration
# ==============================
CURRENT_DIR="$(pwd)"
SERVICE_NAME="llm_gateway"
PYTHON_VERSION="python3"
VENV_PATH="${CURRENT_DIR}/.venv"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "[1/6] Updating system..."
sudo apt update -y && sudo apt install -y build-essential git wget curl unzip ${PYTHON_VERSION}-venv ${PYTHON_VERSION}-dev cmake libomp-dev

echo "[2/6] Creating virtual environment in current directory..."
if [ ! -d "${VENV_PATH}" ]; then
  ${PYTHON_VERSION} -m venv "${VENV_PATH}"
fi
source "${VENV_PATH}/bin/activate"

echo "[3/6] Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

echo "[4/6] Installing Python dependencies..."
if [ -f "${CURRENT_DIR}/requirements.txt" ]; then
  pip install -r "${CURRENT_DIR}/requirements.txt"
else
  echo "❌ requirements.txt not found in ${CURRENT_DIR}"
  exit 1
fi

echo "[5/6] Registering systemd service..."
TMP_SERVICE_FILE=$(mktemp)
sed "s|/home/ubuntu/llm_gateway|${CURRENT_DIR}|g" "${CURRENT_DIR}/llm_gateway.service" > "$TMP_SERVICE_FILE"
sudo cp "$TMP_SERVICE_FILE" "$SYSTEMD_PATH"
rm "$TMP_SERVICE_FILE"

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "[6/6] Setup complete!"
echo "Use './manage.sh start' to run the gateway."
