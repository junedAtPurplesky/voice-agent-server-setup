#!/usr/bin/env bash
set -e

# Dynamically resolve directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env if it exists
if [ -f "${CURRENT_DIR}/.env" ]; then
  set -a
  source "${CURRENT_DIR}/.env"
  set +a
fi

APP_PATH="${CURRENT_DIR}/gateway.py"
VENV_BIN="${CURRENT_DIR}/.venv/bin"

# Fallbacks if not in .env
HOST="${GATEWAY_HOST:-0.0.0.0}"
PORT="${GATEWAY_PORT:-8080}"
WORKERS="${GATEWAY_WORKERS:-1}"  # ✅ Default to 1 if not set

echo "🚀 Starting Gateway on ${HOST}:${PORT} (workers: ${WORKERS})"
exec "${VENV_BIN}/uvicorn" "gateway:app" --host "${HOST}" --port "${PORT}" --workers "${WORKERS}"
