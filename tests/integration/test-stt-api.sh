#!/bin/bash
# Integration test for STT API

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/config/stt.env"

echo "Testing STT API..."

# Create test audio
python3 << PYTHON
import numpy as np
from scipy.io import wavfile
duration = 3
sample_rate = 16000
t = np.linspace(0, duration, int(sample_rate * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
wavfile.write('/tmp/test_stt_api.wav', sample_rate, audio)
print("✓ Test audio created")
PYTHON

# Test health endpoint
echo ""
echo "[1/3] Testing health endpoint..."
curl -s -f "http://localhost:$STT_SERVICE_PORT/health" | jq . && echo "✓ Health check passed" || echo "✗ Health check failed"

# Test transcription endpoint
echo ""
echo "[2/3] Testing transcription endpoint..."
curl -s -X POST "http://localhost:$STT_SERVICE_PORT/transcribe?language=hi" \
  -H "Authorization: Bearer $STT_API_KEY" \
  -F "file=@/tmp/test_stt_api.wav" | jq . && echo "✓ Transcription test passed" || echo "✗ Transcription test failed"

# Test invalid auth
echo ""
echo "[3/3] Testing invalid auth..."
RESPONSE=$(curl -s -X POST "http://localhost:$STT_SERVICE_PORT/transcribe" \
  -H "Authorization: Bearer invalid_key" \
  -F "file=@/tmp/test_stt_api.wav" \
  -w "\n%{http_code}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" == "401" ]; then
    echo "✓ Auth validation works (got 401)"
else
    echo "✗ Auth validation failed (expected 401, got $HTTP_CODE)"
fi

# Cleanup
rm -f /tmp/test_stt_api.wav

echo ""
echo "✓ STT API integration tests complete"
