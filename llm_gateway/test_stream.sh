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

# Fallbacks
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
TEST_API_KEY="${TEST_API_KEY:-test-key}"

echo "🧪 Testing Gateway Streaming..."
echo "Gateway: ${GATEWAY_URL}"
echo ""

cd "${CURRENT_DIR}"

# Check if built
if [ ! -d "${CURRENT_DIR}/dist" ]; then
  echo "🔨 Building TypeScript first..."
  npm run build
fi

# Run test
GATEWAY_URL="${GATEWAY_URL}" TEST_API_KEY="${TEST_API_KEY}" node dist/test-stream.js

