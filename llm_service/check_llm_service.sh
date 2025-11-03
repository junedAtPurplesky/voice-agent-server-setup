#!/usr/bin/env bash
set -e

SERVICE_NAME="llm_service"
SERVICE_URL="http://127.0.0.1:8000"
HEALTH_ENDPOINT="$SERVICE_URL/health"
CHAT_ENDPOINT="$SERVICE_URL/v1/chat/completions"

# ==============================
# Helper Functions
# ==============================

check_health() {
  echo "🔍 Checking service health..."
  if curl -s --fail "$HEALTH_ENDPOINT" > /dev/null; then
    echo "✅ LLM service is healthy and reachable at $HEALTH_ENDPOINT"
  else
    echo "❌ LLM service is not responding or unhealthy."
  fi
  echo
}

check_system_resources() {
  echo "🧠 System Resource Usage"
  echo "-----------------------"
  echo "CPU Load:"
  uptime
  echo
  echo "Memory Usage:"
  free -h
  echo
  echo "Disk Usage:"
  df -h /
  echo
  echo "Top Processes by Memory:"
  ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -n 10
  echo

  if command -v nvidia-smi >/dev/null 2>&1; then
    echo "🎮 GPU Status:"
    nvidia-smi
    echo
  else
    echo "⚠️  No NVIDIA GPU detected (or 'nvidia-smi' not installed)."
    echo
  fi
}

check_service_status() {
  echo "🔧 Checking systemd service: $SERVICE_NAME"
  sudo systemctl is-active --quiet $SERVICE_NAME && echo "✅ Active" || echo "❌ Inactive"
  echo
  sudo systemctl status $SERVICE_NAME --no-pager | head -n 10
  echo
}

view_logs() {
  echo "📜 Recent service logs (last 30 lines):"
  sudo journalctl -u $SERVICE_NAME -n 30 --no-pager
  echo
}

test_inference() {
  echo "💬 Running sample inference..."
  RESPONSE=$(curl -s -X POST "$CHAT_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "qwen2.5-0.5b-instruct",
      "messages": [{"role":"user","content":"What is 2 + 2?"}],
      "max_tokens": 50
    }')

  if [[ "$RESPONSE" == *"content"* ]]; then
    echo "✅ Model responded successfully:"
    echo "$RESPONSE" | jq '.choices[0].message.content' 2>/dev/null || echo "$RESPONSE"
  else
    echo "❌ Model did not respond properly:"
    echo "$RESPONSE"
  fi
  echo
}

load_test() {
  echo "⚡ Performing basic load test..."
  CONCURRENCY=${1:-5}
  REQUESTS=${2:-20}

  if ! command -v hey >/dev/null 2>&1; then
    echo "Installing 'hey' load testing tool..."
    curl -sL https://hey-release.s3.us-east-2.amazonaws.com/hey_linux_amd64 -o /usr/local/bin/hey
    chmod +x /usr/local/bin/hey
  fi

  hey -n "$REQUESTS" -c "$CONCURRENCY" -m POST \
    -T "application/json" \
    -d '{"model":"qwen2.5-0.5b-instruct","messages":[{"role":"user","content":"Tell me a joke."}],"max_tokens":20}' \
    "$CHAT_ENDPOINT"
  echo
}

# ==============================
# Interactive Menu
# ==============================

while true; do
  clear
  echo "=========================================="
  echo "🧩 LLM Service Diagnostic & Health Utility"
  echo "=========================================="
  echo "1️⃣  Check Service Health"
  echo "2️⃣  Check System Resources"
  echo "3️⃣  Check Systemd Service Status"
  echo "4️⃣  View Logs"
  echo "5️⃣  Test Inference"
  echo "6️⃣  Run Load Test"
  echo "7️⃣  Exit"
  echo "------------------------------------------"
  read -rp "Choose an option [1-7]: " opt

  case $opt in
    1) check_health ;;
    2) check_system_resources ;;
    3) check_service_status ;;
    4) view_logs ;;
    5) test_inference ;;
    6)
      read -rp "Enter concurrency (default 5): " c
      read -rp "Enter total requests (default 20): " n
      load_test "${c:-5}" "${n:-20}"
      ;;
    7) echo "👋 Exiting..."; exit 0 ;;
    *) echo "❌ Invalid option";;
  esac
  read -rp "Press ENTER to continue..."
done
