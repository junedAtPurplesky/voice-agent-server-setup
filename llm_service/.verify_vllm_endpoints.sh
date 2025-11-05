#!/usr/bin/env bash
# Quick script to verify all vLLM endpoints

echo "🔍 Verifying vLLM API Endpoints"
echo "================================"

BASE_URL="${LLM_URL:-http://127.0.0.1:8000}"

echo ""
echo "1. Testing /v1/models endpoint..."
curl -s "$BASE_URL/v1/models" | jq '.' && echo "✅ /v1/models works" || echo "❌ /v1/models failed"

echo ""
echo "2. Testing /health endpoint (optional)..."
curl -s "$BASE_URL/health" && echo "✅ /health works" || echo "⚠️  /health not available (optional)"

echo ""
echo "3. Testing /version endpoint (optional)..."
curl -s "$BASE_URL/version" && echo "✅ /version works" || echo "⚠️  /version not available (optional)"

echo ""
echo "4. Testing /v1/completions endpoint..."
MODEL=$(curl -s "$BASE_URL/v1/models" | jq -r '.data[0].id')
if [ -n "$MODEL" ]; then
    curl -s -X POST "$BASE_URL/v1/completions" \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"Test\",
        \"max_tokens\": 5
      }" | jq '.' && echo "✅ /v1/completions works" || echo "❌ /v1/completions failed"
else
    echo "❌ Could not get model name"
fi

echo ""
echo "5. Testing /v1/chat/completions endpoint..."
if [ -n "$MODEL" ]; then
    curl -s -X POST "$BASE_URL/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"$MODEL\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}],
        \"max_tokens\": 5
      }" | jq '.' && echo "✅ /v1/chat/completions works" || echo "❌ /v1/chat/completions failed"
else
    echo "❌ Could not get model name"
fi

echo ""
echo "================================"
echo "✅ Endpoint verification complete!"
