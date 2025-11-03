#!/usr/bin/env bash
set -e

# Dynamically resolve directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${CURRENT_DIR}/.env"

APP_PATH="${CURRENT_DIR}/gateway.py"
VENV_BIN="${CURRENT_DIR}/.venv/bin"

HOST="${GATEWAY_HOST:-0.0.0.0}"
PORT="${GATEWAY_PORT:-8080}"

exec "${VENV_BIN}/uvicorn" gateway:app --host "$HOST" --port "$PORT" --workers 1
