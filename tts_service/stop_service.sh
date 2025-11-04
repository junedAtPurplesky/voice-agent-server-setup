#!/bin/bash

set -e

echo "Stopping CosyVoice2 TTS Service..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.tts_service.pid"

# Find and kill the service
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping service (PID: $PID)..."
        kill $PID
        
        # Wait for graceful shutdown
        sleep 2
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force stopping..."
            kill -9 $PID
        fi
        
        rm -f "$PID_FILE"
        echo "Service stopped."
    else
        echo "Service is not running (stale PID file)."
        rm -f "$PID_FILE"
    fi
else
    # Try to find by process name
    PID=$(ps aux | grep "python3 tts_server.py" | grep -v grep | awk '{print $2}')
    
    if [ ! -z "$PID" ]; then
        echo "Found service (PID: $PID), stopping..."
        kill $PID
        sleep 2
        
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
        fi
        echo "Service stopped."
    else
        echo "Service is not running."
    fi
fi

