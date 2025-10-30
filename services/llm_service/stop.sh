#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$BASE_DIR/pids/llm.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill -TERM "$PID"
        echo "LLM service stopped"
    fi
    rm -f "$PID_FILE"
fi
