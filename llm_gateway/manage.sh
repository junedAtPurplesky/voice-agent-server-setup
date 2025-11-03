#!/usr/bin/env bash
set -e

CURRENT_DIR="$(pwd)"
SERVICE="llm_gateway"
LOG_PATH="${CURRENT_DIR}/gateway.log"
PID_FILE="${CURRENT_DIR}/${SERVICE}.pid"
RUN_CMD="bash ${CURRENT_DIR}/start_gateway.sh"

function start_service() {
  if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "⚠️  $SERVICE is already running (PID: $(cat "$PID_FILE"))."
    return
  fi

  echo "🚀 Starting $SERVICE..."
  nohup $RUN_CMD > "$LOG_PATH" 2>&1 &
  echo $! > "$PID_FILE"
  echo "✅ Started (PID: $(cat "$PID_FILE")) — logs: $LOG_PATH"
}

function stop_service() {
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      echo "🛑 Stopping $SERVICE (PID: $PID)..."
      kill "$PID"
      rm -f "$PID_FILE"
      echo "✅ Stopped."
    else
      echo "⚠️  PID file found but process not running. Cleaning up..."
      rm -f "$PID_FILE"
    fi
  else
    echo "❌ $SERVICE is not running."
  fi
}

function restart_service() {
  stop_service
  start_service
}

function status_service() {
  if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ $SERVICE is running (PID: $(cat "$PID_FILE"))"
  else
    echo "🛑 $SERVICE is not running."
  fi
}

function view_logs() {
  echo "📜 Viewing live logs from $LOG_PATH..."
  tail -f "$LOG_PATH"
}

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
  echo "  5) View Live Logs"
  echo "  6) Exit"
  echo "==============================================="
  echo ""
  read -p "Enter choice [1-6]: " choice
  handle_choice "$choice"
}

function handle_choice() {
  case "$1" in
    1) start_service ;;
    2) stop_service ;;
    3) restart_service ;;
    4) status_service ;;
    5) view_logs ;;
    6) echo "👋 Exiting." ; exit 0 ;;
    *) echo "❌ Invalid choice." ;;
  esac
}

# Allow both interactive and direct CLI usage
if [ $# -eq 0 ]; then
  show_menu
else
  handle_choice "$1"
fi
