#!/usr/bin/env bash
#
# Full Stack Integration Test
# Tests the gateway with a mock vLLM server
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if exists
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Configuration
MOCK_VLLM_PORT="${MOCK_VLLM_PORT:-8000}"
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
TEST_API_KEY="${TEST_API_KEY:-test-key}"

echo "═══════════════════════════════════════════════════════════"
echo "🧪 Full Stack Integration Test"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "This will test the complete stack:"
echo "  1. Mock vLLM Server (port $MOCK_VLLM_PORT)"
echo "  2. Gateway (port $GATEWAY_PORT)"
echo "  3. Streaming verification"
echo ""

# Check if build exists
if [ ! -d "dist" ]; then
  echo "📦 Building project first..."
  npm run build
  echo ""
fi

# Kill any existing processes on our ports
echo "🧹 Cleaning up any existing processes..."
lsof -ti:$MOCK_VLLM_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$GATEWAY_PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start mock vLLM server
echo "🤖 Starting Mock vLLM Server on port $MOCK_VLLM_PORT..."
MOCK_VLLM_PORT=$MOCK_VLLM_PORT node dist/mock-vllm-server.js > /tmp/mock-vllm.log 2>&1 &
MOCK_PID=$!
echo "   PID: $MOCK_PID"

# Wait for mock vLLM to be ready
sleep 2
if ! kill -0 $MOCK_PID 2>/dev/null; then
  echo "❌ Mock vLLM failed to start!"
  cat /tmp/mock-vllm.log
  exit 1
fi

# Check if mock is responding
if ! curl -s http://localhost:$MOCK_VLLM_PORT/health > /dev/null; then
  echo "❌ Mock vLLM not responding!"
  kill $MOCK_PID 2>/dev/null || true
  exit 1
fi
echo "   ✅ Mock vLLM is ready"
echo ""

# Start gateway
echo "🚀 Starting Gateway on port $GATEWAY_PORT..."
VLLM_BASE="http://localhost:$MOCK_VLLM_PORT" \
GATEWAY_PORT=$GATEWAY_PORT \
ALLOWED_API_KEYS="$TEST_API_KEY" \
node dist/gateway.js > /tmp/gateway.log 2>&1 &
GATEWAY_PID=$!
echo "   PID: $GATEWAY_PID"

# Wait for gateway to be ready
sleep 2
if ! kill -0 $GATEWAY_PID 2>/dev/null; then
  echo "❌ Gateway failed to start!"
  cat /tmp/gateway.log
  kill $MOCK_PID 2>/dev/null || true
  exit 1
fi

# Check if gateway is responding
if ! curl -s http://localhost:$GATEWAY_PORT/healthz > /dev/null; then
  echo "❌ Gateway not responding!"
  kill $GATEWAY_PID 2>/dev/null || true
  kill $MOCK_PID 2>/dev/null || true
  exit 1
fi
echo "   ✅ Gateway is ready"
echo ""

# Run integration tests
echo "🧪 Running Integration Tests..."
echo ""
GATEWAY_URL="http://localhost:$GATEWAY_PORT" \
TEST_API_KEY="$TEST_API_KEY" \
node dist/integration-test.js

TEST_EXIT_CODE=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $GATEWAY_PID 2>/dev/null || true
kill $MOCK_PID 2>/dev/null || true
sleep 1

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "✅ ALL TESTS PASSED!"
  echo "═══════════════════════════════════════════════════════════"
  echo ""
  echo "Your gateway is working correctly and safe to deploy! 🚀"
  echo ""
  echo "Next steps:"
  echo "  1. Deploy to your cloud environment"
  echo "  2. Update VLLM_BASE to point to your real vLLM server"
  echo "  3. Set production API keys in ALLOWED_API_KEYS"
  echo "  4. Run this test again in your cloud environment"
  echo ""
  exit 0
else
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "❌ TESTS FAILED"
  echo "═══════════════════════════════════════════════════════════"
  echo ""
  echo "Check the logs above for details."
  echo "Logs saved to:"
  echo "  - /tmp/mock-vllm.log"
  echo "  - /tmp/gateway.log"
  echo ""
  exit 1
fi

