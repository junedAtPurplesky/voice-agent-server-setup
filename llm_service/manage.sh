#!/usr/bin/env bash
set -e

CURRENT_DIR="$(pwd)"
VENV_PATH="${CURRENT_DIR}/.venv"
LOG_FILE="${CURRENT_DIR}/llm_service.log"
ERR_FILE="${CURRENT_DIR}/llm_service.err"
SERVICE_CMD="vllm serve"

show_menu() {
  echo ""
  echo "========= LLM Service Manager ========="
  echo "1) Start Service"
  echo "2) Stop Service"
  echo "3) Check Status"
  echo "4) View Logs"
  echo "5) View Error Logs"
  echo "6) Exit"
  echo "======================================"
  echo ""
  read -rp "Enter choice [1-6]: " choice
  handle_choice "$choice"
}

handle_choice() {
  case "$1" in
    1)
      echo "🚀 Starting LLM service..."
      source "${VENV_PATH}/bin/activate"
      if [ -f "${CURRENT_DIR}/vllm_config.sh" ]; then
        source "${CURRENT_DIR}/vllm_config.sh"
        nohup bash -c "eval \"$VLLM_CMD\"" > "$LOG_FILE" 2> "$ERR_FILE" &
        echo "✅ LLM started (PID: $!) | Logs: $LOG_FILE"
      else
        echo "❌ vllm_config.sh not found."
      fi
      ;;
    2)
      echo "🛑 Stopping LLM service..."
      pkill -f "$SERVICE_CMD" || echo "No running LLM service found."
      echo "✅ LLM stopped."
      ;;
    3)
      echo "🔍 Checking LLM status..."
      if pgrep -f "$SERVICE_CMD" > /dev/null; then
        echo "✅ LLM service is running."
      else
        echo "❌ LLM service is not running."
      fi
      ;;
    4)
      tail -f "$LOG_FILE"
      ;;
    5)
      tail -f "$ERR_FILE"
      ;;
    6)
      echo "👋 Exiting."
      exit 0
      ;;
    *)
      echo "❌ Invalid choice."
      ;;
  esac
}

if [ $# -eq 0 ]; then
  show_menu
else
  handle_choice "$1"
fi
