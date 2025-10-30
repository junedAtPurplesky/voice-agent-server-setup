#!/bin/bash
# Integration test for LLM API

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/config/llm.env"

echo "Testing LLM API..."

# Test health endpoint
echo "[1/3] Testing health endpoint..."
curl -s -f "http://localhost:$LLM_SERVICE_PORT/health" | jq . && echo "✓ Health check passed" || echo "✗ Health check failed"

# Test chat completion endpoint
echo ""
echo "[2/3] Testing chat completion endpoint..."
RESPONSE=$(curl -s -X POST "http://localhost:$LLM_SERVICE_PORT/v1/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
    "messages": [
      {"role": "system", "content": "You are helpful."},
      {"role": "user", "content": "Say hi in 3 words."}
    ],
    "max_tokens": 20
  }')

if echo "$RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
    echo "✓ Chat completion test passed"
    echo "  Response: $CONTENT"
else
    echo "✗ Chat completion test failed"
fi

# Test invalid auth
echo ""
echo "[3/3] Testing invalid auth..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "http://localhost:$LLM_SERVICE_PORT/v1/chat/completions" \
  -H "Authorization: Bearer invalid_key" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}')
if [ "$HTTP_CODE" == "401" ]; then
    echo "✓ Auth validation works (got 401)"
else
    echo "✗ Auth validation failed (expected 401, got $HTTP_CODE)"
fi

echo ""
echo "✓ LLM API integration tests complete"
