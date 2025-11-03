#!/usr/bin/env bash
# Compare Python vs Node.js gateway performance

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
API_KEY="${1:-test-key}"
ITERATIONS="${2:-5}"

echo "═══════════════════════════════════════════════════════════"
echo "🔬 Gateway Performance Comparison"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "URL: $GATEWAY_URL"
echo "Iterations: $ITERATIONS"
echo ""

# Test payload
PAYLOAD='{
  "model": "Qwen/Qwen2.5-0.5B-Instruct-AWQ",
  "temperature": 0.7,
  "max_tokens": 64,
  "stream": true,
  "messages": [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Explain transformers in simple terms."}
  ]
}'

echo "📋 Test Configuration:"
echo "   Model: Qwen/Qwen2.5-0.5B-Instruct-AWQ"
echo "   Max Tokens: 64"
echo "   Stream: true"
echo ""

# Function to test streaming
test_streaming() {
  local iteration=$1
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Test #$iteration"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  # Measure time to first chunk and total time
  START_TIME=$(date +%s%N)
  FIRST_CHUNK_TIME=""
  CHUNK_COUNT=0
  
  # Create temporary file for output
  TEMP_FILE=$(mktemp)
  
  # Run curl and capture output
  {
    curl -N -X POST "${GATEWAY_URL}/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d "$PAYLOAD" \
      -w "\n\n--- Response Info ---\nHTTP Code: %{http_code}\nTime Total: %{time_total}s\nTime to First Byte: %{time_starttransfer}s\n" \
      2>/dev/null | tee "$TEMP_FILE"
  } &
  
  CURL_PID=$!
  
  # Monitor for first chunk
  while kill -0 $CURL_PID 2>/dev/null; do
    if [ -z "$FIRST_CHUNK_TIME" ] && [ -s "$TEMP_FILE" ]; then
      FIRST_CHUNK_TIME=$(date +%s%N)
      FIRST_CHUNK_MS=$(( (FIRST_CHUNK_TIME - START_TIME) / 1000000 ))
      echo ""
      echo "⚡ First chunk received in: ${FIRST_CHUNK_MS}ms"
      break
    fi
    sleep 0.001
  done
  
  wait $CURL_PID
  
  # Count chunks
  CHUNK_COUNT=$(grep -c "^data:" "$TEMP_FILE" || echo 0)
  
  END_TIME=$(date +%s%N)
  TOTAL_MS=$(( (END_TIME - START_TIME) / 1000000 ))
  
  echo ""
  echo "📊 Results:"
  echo "   Total time: ${TOTAL_MS}ms"
  echo "   Chunks received: $CHUNK_COUNT"
  if [ -n "$FIRST_CHUNK_TIME" ]; then
    echo "   First chunk latency: ${FIRST_CHUNK_MS}ms"
    AVG_CHUNK_TIME=$(( (TOTAL_MS - FIRST_CHUNK_MS) / CHUNK_COUNT ))
    echo "   Avg time per chunk: ${AVG_CHUNK_TIME}ms"
  fi
  
  # Check for [DONE]
  if grep -q "data: \[DONE\]" "$TEMP_FILE"; then
    echo "   ✅ Stream completed with [DONE]"
  else
    echo "   ⚠️  No [DONE] marker found"
  fi
  
  rm -f "$TEMP_FILE"
  echo ""
}

# Run tests
TOTAL_FIRST_CHUNK=0
TOTAL_TIME=0
SUCCESS_COUNT=0

for i in $(seq 1 $ITERATIONS); do
  if test_streaming $i; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  fi
  
  if [ $i -lt $ITERATIONS ]; then
    echo "⏳ Cooling down 2s..."
    sleep 2
  fi
done

echo "═══════════════════════════════════════════════════════════"
echo "📈 Summary"
echo "═══════════════════════════════════════════════════════════"
echo "Successful tests: $SUCCESS_COUNT / $ITERATIONS"
echo ""
echo "✅ Testing complete!"
echo ""
echo "💡 Tips:"
echo "   • Lower first chunk latency = better streaming"
echo "   • Should see chunks immediately, not all at once"
echo "   • Compare Python vs Node.js by switching GATEWAY_PORT"
echo ""
echo "Example: Test both implementations"
echo "   Python:  GATEWAY_URL=http://localhost:8080 ./compare-implementations.sh"
echo "   Node.js: GATEWAY_URL=http://localhost:8081 ./compare-implementations.sh"

