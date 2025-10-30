#!/bin/bash
################################################################################
# Install All Python Dependencies
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/venv/bin/activate"

echo "Installing Python dependencies..."

# Common dependencies
echo "  → Installing common packages..."
pip install -q --upgrade pip setuptools wheel
pip install -q \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    websockets==12.0 \
    pydantic==2.5.0 \
    python-multipart==0.0.6 \
    python-dotenv==1.0.0 \
    numpy==1.24.0 \
    scipy==1.11.0

# PyTorch
echo "  → Installing PyTorch with CUDA 12.1..."
pip install -q \
    torch==2.1.0 \
    torchaudio==2.1.0

# STT dependencies
echo "  → Installing STT (Faster Whisper) dependencies..."
pip install -q faster-whisper==1.0.3

# TTS dependencies
echo "  → Installing TTS (CosyVoice2) dependencies..."
if [ ! -d "$BASE_DIR/cosyvoice" ]; then
    echo "  → Cloning CosyVoice..."
    git clone -q https://github.com/FunAudioLLM/CosyVoice.git "$BASE_DIR/cosyvoice"
fi
cd "$BASE_DIR/cosyvoice" && pip install -q -e . && cd "$BASE_DIR"

# LLM dependencies
echo "  → Installing LLM (vLLM) dependencies..."
pip install -q \
    vllm==0.4.0 \
    transformers==4.36.0

echo "✓ All Python dependencies installed"
