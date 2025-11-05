#!/bin/bash

set -e

echo "=========================================="
echo "Starting CosyVoice TTS Service"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: Conda is not installed!"
    echo "Please install Conda and run ./setup.sh"
    exit 1
fi

# Get conda base
CONDA_BASE=$(conda info --base)

# Activate conda environment
echo "Activating conda environment 'cosyvoice'..."
source "${CONDA_BASE}/etc/profile.d/conda.sh"

if ! conda env list | grep -q "^cosyvoice "; then
    echo "Error: Conda environment 'cosyvoice' not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

conda activate cosyvoice

echo "✓ Environment activated"
echo "  Python: $(which python)"
echo "  Python version: $(python --version)"

# Check if CosyVoice is available
echo ""
echo "Checking CosyVoice installation..."
python -c "from cosyvoice.cli.cosyvoice import CosyVoice" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: CosyVoice not properly installed!"
    echo "Please run ./setup.sh to install CosyVoice"
    exit 1
fi
echo "✓ CosyVoice installed"

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

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "GPU Information:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    echo ""
fi

# Set environment variables for optimal performance
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

echo ""
echo "Starting TTS service..."
echo "  Host: 0.0.0.0"
echo "  Port: 8002"
echo "  Model: CosyVoice-300M-SFT"
echo ""
echo "Note: First startup will download the model (~1GB)"
echo "      This may take several minutes..."
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
    echo "Service is running at: http://localhost:8002"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    tail -f tts_service.log"
    echo "  Health check: curl http://localhost:8002/health"
    echo "  List voices:  curl http://localhost:8002/voices"
    echo "  Stop service: ./stop_service.sh"
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
