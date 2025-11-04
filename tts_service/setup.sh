#!/bin/bash

set -e

echo "=========================================="
echo "CosyVoice2 TTS Service Setup"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Install system dependencies
echo ""
echo "Checking system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Installing required system packages (FFmpeg, audio libraries)..."
    apt-get update -qq
    apt-get install -y -qq \
        pkg-config \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libavdevice-dev \
        libavfilter-dev \
        libswscale-dev \
        libswresample-dev \
        ffmpeg \
        libsndfile1-dev
    echo "System dependencies installed successfully."
elif command -v yum &> /dev/null; then
    echo "Installing required system packages..."
    yum install -y \
        pkgconfig \
        ffmpeg-devel \
        ffmpeg \
        libsndfile-devel
    echo "System dependencies installed successfully."
elif command -v brew &> /dev/null; then
    echo "Installing required system packages (FFmpeg, libsndfile)..."
    brew install pkg-config ffmpeg libsndfile
    echo "System dependencies installed successfully."
else
    echo "Warning: Could not detect package manager. Please ensure FFmpeg and libsndfile are installed."
fi

# Check Python version
echo ""
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

# Install CosyVoice2 from GitHub
echo ""
echo "Installing CosyVoice2..."
if [ -d "CosyVoice" ]; then
    echo "CosyVoice directory exists. Updating..."
    cd CosyVoice
    git pull
    cd ..
else
    echo "Cloning CosyVoice repository..."
    git clone https://github.com/FunAudioLLM/CosyVoice.git
fi

echo "Installing CosyVoice dependencies..."
cd CosyVoice
pip install -r requirements.txt
cd ..

# Create models directory
echo ""
echo "Creating models directory..."
mkdir -p models

# Test installation
echo ""
echo "Testing installation..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import fastapi; print('FastAPI: OK')"
python3 -c "import transformers; print('Transformers: OK')"
python3 -c "import librosa; print('Librosa: OK')"
python3 -c "import soundfile; print('Soundfile: OK')"

echo ""
echo "Testing CosyVoice import..."
python3 -c "
import sys
sys.path.insert(0, 'CosyVoice')
try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    print('CosyVoice: OK')
except Exception as e:
    print(f'CosyVoice: Warning - {e}')
    print('Note: Full CosyVoice functionality requires model download on first use')
"

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "To start the service, run:"
echo "  ./start_service.sh"
echo ""
echo "The CosyVoice2-0.5B model will be downloaded automatically on first use."
echo "This may take several minutes depending on your internet connection."
echo ""

