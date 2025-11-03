#!/usr/bin/env bash
set -e

CURRENT_DIR="$(pwd)"
SERVICE="llm_gateway"
LOG_PATH="${CURRENT_DIR}/gateway.log"

function show_menu() {
  echo ""
  echo "========= vLLM Gateway Service Manager ========="
  echo "Service: $SERVICE"
  echo ""
  echo "Select an option:"
  echo "  1) Start Service"
  echo "  2) Stop Service"
  echo "  3) Restart Service"
  echo "  4) Check Status"
  echo "  5) View Live Logs (journalctl)"
  echo "  6) Tail Log File ($LOG_PATH)"
  echo "  7) Enable on Boot"
  echo "  8) Disable on Boot"
  echo "  9) Exit"
  echo "==============================================="
  echo ""
  read -p "Enter choice [1-9]: " choice
  handle_choice "$choice"
}

function handle_choice() {
  case "$1" in
    1)
      sudo systemctl start "$SERVICE"
      echo "✅ Gateway started."
      ;;
    2)
      sudo systemctl stop "$SERVICE"
      echo "🛑 Gateway stopped."
      ;;
    3)
      sudo systemctl restart "$SERVICE"
      echo "🔄 Gateway restarted."
      ;;
    4)
      sudo systemctl status "$SERVICE" --no-pager
      ;;
    5)
      sudo journalctl -u "$SERVICE" -f
      ;;
    6)
      tail -f "$LOG_PATH"
      ;;
    7)
      sudo systemctl enable "$SERVICE"
      echo "📦 Gateway enabled on boot."
      ;;
    8)
      sudo systemctl disable "$SERVICE"
      echo "🚫 Gateway disabled from boot."
      ;;
    9)
      echo "👋 Exiting."
      exit 0
      ;;
    *)
      echo "❌ Invalid choice."
      ;;
  esac
}

# Allow both interactive and direct CLI usage
if [ $# -eq 0 ]; then
  show_menu
else
  handle_choice "$1"
fi
