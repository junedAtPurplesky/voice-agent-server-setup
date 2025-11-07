#!/bin/bash

set -e

echo "=========================================="
echo "Starting Piper TTS Service"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "✓ Environment activated"
echo "  Python: $(which python)"
echo "  Python version: $(python --version)"

# Check if Piper is installed
echo ""
echo "Checking Piper installation..."
python -c "import piper" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Warning: Piper not installed via pip"
    echo "Service will attempt to use system Piper binary"
fi

# Check if service is already running
if [ -f ".service.pid" ]; then
    PID=$(cat .service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo ""
        echo "Service is already running (PID: $PID)"
        echo "To restart, run: ./stop_service.sh && ./start_service.sh"
        exit 0
    else
        echo "Removing stale PID file..."
        rm .service.pid
    fi
fi

# Check for GPU (optional for Piper)
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "GPU Information:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    echo ""
fi

# Set environment variables
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

echo ""
echo "Starting TTS service..."
echo "  Host: 0.0.0.0"
echo "  Port: 8003"
echo "  Engine: Piper TTS"
echo "  Languages: Hindi, English"
echo ""
echo "Note: Voice models will be downloaded on first use"
echo "      (~10-50MB per voice model)"
echo ""

# Start service in background
nohup python tts_server.py > tts_service.log 2>&1 &
PID=$!

# Save PID
echo $PID > .service.pid

# Wait a moment and check if it started
echo "Waiting for service to start..."
sleep 3

if ps -p $PID > /dev/null 2>&1; then
    echo "✓ Service started successfully (PID: $PID)"
    echo ""
    echo "Service is running at: http://localhost:8003"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    tail -f tts_service.log"
    echo "  Health check: curl http://localhost:8003/health"
    echo "  List voices:  curl http://localhost:8003/voices"
    echo "  Stop service: ./stop_service.sh"
    echo ""
    echo "Test the service:"
    echo "  python test_client.py"
    echo ""
else
    echo "✗ Service failed to start"
    echo ""
    echo "Check logs for errors:"
    echo "  cat tts_service.log"
    echo ""
    rm .service.pid
    exit 1
fi

