#!/bin/bash
# Integration test for TTS API

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/config/tts.env"

echo "Testing TTS API..."

# Test health endpoint
echo "[1/3] Testing health endpoint..."
curl -s -f "http://localhost:$TTS_SERVICE_PORT/health" | jq . && echo "✓ Health check passed" || echo "✗ Health check failed"

# Test synthesis endpoint
echo ""
echo "[2/3] Testing synthesis endpoint..."
curl -s -X POST "http://localhost:$TTS_SERVICE_PORT/synthesize?text=hello&language=en" \
  -H "Authorization: Bearer $TTS_API_KEY" \
  -o /tmp/test_tts_output.wav
if [ -f /tmp/test_tts_output.wav ] && [ -s /tmp/test_tts_output.wav ]; then
    SIZE=$(stat -f%z /tmp/test_tts_output.wav 2>/dev/null || stat -c%s /tmp/test_tts_output.wav)
    echo "✓ Synthesis test passed (output: ${SIZE} bytes)"
else
    echo "✗ Synthesis test failed"
fi

# Test invalid auth
echo ""
echo "[3/3] Testing invalid auth..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "http://localhost:$TTS_SERVICE_PORT/synthesize?text=test" \
  -H "Authorization: Bearer invalid_key")
if [ "$HTTP_CODE" == "401" ]; then
    echo "✓ Auth validation works (got 401)"
else
    echo "✗ Auth validation failed (expected 401, got $HTTP_CODE)"
fi

# Cleanup
rm -f /tmp/test_tts_output.wav

echo ""
echo "✓ TTS API integration tests complete"
