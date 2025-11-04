#!/bin/bash

set -e

echo "=========================================="
echo "Faster Whisper STT Service Setup"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Install system dependencies required for PyAV
echo ""
echo "Checking system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Installing required system packages (pkg-config, FFmpeg libraries)..."
    apt-get update -qq
    apt-get install -y -qq pkg-config \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libavdevice-dev \
        libavfilter-dev \
        libswscale-dev \
        libswresample-dev \
        ffmpeg
    echo "System dependencies installed successfully."
elif command -v yum &> /dev/null; then
    echo "Installing required system packages (pkg-config, FFmpeg libraries)..."
    yum install -y pkgconfig \
        ffmpeg-devel \
        ffmpeg
    echo "System dependencies installed successfully."
elif command -v brew &> /dev/null; then
    echo "Installing required system packages (pkg-config, FFmpeg)..."
    brew install pkg-config ffmpeg
    echo "System dependencies installed successfully."
else
    echo "Warning: Could not detect package manager. Please ensure pkg-config and FFmpeg libraries are installed."
fi

# Check Python version
echo "Checking Python version..."
PYTHON_CMD=""
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" > "3.8" ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
echo "Virtual environment created."

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA support if available
echo ""
echo "Installing PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing PyTorch with CUDA support..."
    pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121
else
    echo "No NVIDIA GPU detected. Installing CPU version..."
    pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cpu
fi

# Install other requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create models directory
echo ""
echo "Creating models directory..."
mkdir -p models

# Test installation
echo ""
echo "Testing installation..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import faster_whisper; print('Faster Whisper: OK')"
python3 -c "import fastapi; print('FastAPI: OK')"
python3 -c "import webrtcvad; print('WebRTC VAD: OK')"

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "To start the service, run:"
echo "  ./start_service.sh"
echo ""
echo "The model will be downloaded on first use."
echo ""

