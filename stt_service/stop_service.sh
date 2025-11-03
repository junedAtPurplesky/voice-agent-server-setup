#!/bin/bash

echo "Stopping Faster Whisper STT Service..."

# Find and kill the process
PID=$(ps aux | grep "python3 stt_server.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "Service is not running."
else
    kill -9 $PID
    echo "Service stopped (PID: $PID)"
fi

