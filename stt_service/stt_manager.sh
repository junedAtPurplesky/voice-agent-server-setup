#!/bin/bash

# STT Service Manager Script
# Provides easy management of the Faster Whisper STT service

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

SERVICE_NAME="Faster Whisper STT Service"
PID_FILE="$SCRIPT_DIR/.stt_service.pid"

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        ps aux | grep "python3 stt_server.py" | grep -v grep | awk '{print $2}'
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        return 1
    fi
    if ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

start_service() {
    if is_running; then
        echo "$SERVICE_NAME is already running (PID: $(get_pid))"
        return 0
    fi
    
    echo "Starting $SERVICE_NAME..."
    
    if [ ! -d "venv" ]; then
        echo "Error: Virtual environment not found."
        echo "Please run ./setup.sh first."
        exit 1
    fi
    
    source venv/bin/activate
    
    # Start service in background
    nohup python3 stt_server.py > stt_service.log 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        echo "$SERVICE_NAME started successfully (PID: $pid)"
        echo "Logs: $SCRIPT_DIR/stt_service.log"
    else
        echo "Failed to start $SERVICE_NAME"
        echo "Check logs: $SCRIPT_DIR/stt_service.log"
        exit 1
    fi
}

stop_service() {
    if ! is_running; then
        echo "$SERVICE_NAME is not running."
        rm -f "$PID_FILE"
        return 0
    fi
    
    local pid=$(get_pid)
    echo "Stopping $SERVICE_NAME (PID: $pid)..."
    
    kill $pid
    
    # Wait for graceful shutdown
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    if is_running; then
        echo "Forcing stop..."
        kill -9 $pid
    fi
    
    rm -f "$PID_FILE"
    echo "$SERVICE_NAME stopped."
}

restart_service() {
    echo "Restarting $SERVICE_NAME..."
    stop_service
    sleep 2
    start_service
}

status_service() {
    if is_running; then
        local pid=$(get_pid)
        echo "$SERVICE_NAME is running (PID: $pid)"
        
        # Try to get health status
        if command -v curl &> /dev/null; then
            echo ""
            echo "Health Check:"
            curl -s http://localhost:8001/health | python3 -m json.tool || echo "Service not responding to health check"
        fi
    else
        echo "$SERVICE_NAME is not running."
    fi
}

show_logs() {
    if [ -f "stt_service.log" ]; then
        tail -f stt_service.log
    else
        echo "No log file found."
    fi
}

case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the STT service"
        echo "  stop    - Stop the STT service"
        echo "  restart - Restart the STT service"
        echo "  status  - Check service status"
        echo "  logs    - Show service logs (tail -f)"
        exit 1
        ;;
esac

