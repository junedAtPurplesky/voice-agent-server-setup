#!/bin/bash

set -e

echo "=========================================="
echo "Starting Faster Whisper STT Service"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if running on GPU
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "GPU Information:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    echo ""
fi

# Set environment variables for optimal performance
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# Start the service
echo "Starting STT service on port 8001..."
echo ""

python3 stt_server.py

