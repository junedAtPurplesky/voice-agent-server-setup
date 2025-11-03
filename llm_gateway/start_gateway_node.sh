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

# Fallbacks if not in .env
HOST="${GATEWAY_HOST:-0.0.0.0}"
PORT="${GATEWAY_PORT:-8080}"

echo "🚀 Starting Node.js Gateway on ${HOST}:${PORT}"

# Check if node_modules exists
if [ ! -d "${CURRENT_DIR}/node_modules" ]; then
  echo "📦 Installing dependencies..."
  cd "${CURRENT_DIR}"
  npm install
fi

# Check if dist exists, if not build
if [ ! -d "${CURRENT_DIR}/dist" ]; then
  echo "🔨 Building TypeScript..."
  cd "${CURRENT_DIR}"
  npm run build
fi

cd "${CURRENT_DIR}"
exec npm start

