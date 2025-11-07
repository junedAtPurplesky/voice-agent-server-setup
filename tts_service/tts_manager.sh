#!/bin/bash

# TTS Service Manager Script
# Provides easy management of the CosyVoice2 TTS service

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

SERVICE_NAME="CosyVoice2 TTS Service"
PID_FILE="$SCRIPT_DIR/.tts_service.pid"

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        ps aux | grep "python3 tts_server.py" | grep -v grep | awk '{print $2}'
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
    
    # Add CosyVoice to Python path
    export PYTHONPATH="${SCRIPT_DIR}/CosyVoice:${PYTHONPATH}"
    
    # Start service in background
    nohup python3 tts_server.py > tts_service.log 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    if is_running; then
        echo "$SERVICE_NAME started successfully (PID: $pid)"
        echo "Logs: $SCRIPT_DIR/tts_service.log"
    else
        echo "Failed to start $SERVICE_NAME"
        echo "Check logs: $SCRIPT_DIR/tts_service.log"
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
            curl -s http://localhost:8002/health | python3 -m json.tool || echo "Service not responding to health check"
        fi
    else
        echo "$SERVICE_NAME is not running."
    fi
}

show_logs() {
    if [ -f "tts_service.log" ]; then
        tail -f tts_service.log
    else
        echo "No log file found."
    fi
}

verify_model() {
    echo "Verifying model integrity..."
    echo ""
    
    # Check if conda is available
    if command -v conda &> /dev/null; then
        CONDA_BASE=$(conda info --base)
        source "${CONDA_BASE}/etc/profile.d/conda.sh"
        conda activate cosyvoice 2>/dev/null || true
    fi
    
    # Run verification
    if [ -f "download_model.py" ]; then
        python download_model.py --verify-only
    else
        echo "Error: download_model.py not found"
        exit 1
    fi
}

repair_model() {
    echo "Repairing model (force re-download)..."
    echo ""
    
    # Check if conda is available
    if command -v conda &> /dev/null; then
        CONDA_BASE=$(conda info --base)
        source "${CONDA_BASE}/etc/profile.d/conda.sh"
        conda activate cosyvoice 2>/dev/null || true
    fi
    
    # Stop service if running
    if is_running; then
        echo "Stopping service first..."
        stop_service
        echo ""
    fi
    
    # Force re-download
    if [ -f "download_model.py" ]; then
        python download_model.py --force
        if [ $? -eq 0 ]; then
            echo ""
            echo "Model repaired successfully!"
            echo "You can now start the service:"
            echo "  ./start_service.sh"
        fi
    else
        echo "Error: download_model.py not found"
        exit 1
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
    verify)
        verify_model
        ;;
    repair)
        repair_model
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|verify|repair}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the TTS service"
        echo "  stop    - Stop the TTS service"
        echo "  restart - Restart the TTS service"
        echo "  status  - Check service status"
        echo "  logs    - Show service logs (tail -f)"
        echo "  verify  - Verify model integrity"
        echo "  repair  - Repair/re-download model"
        exit 1
        ;;
esac

