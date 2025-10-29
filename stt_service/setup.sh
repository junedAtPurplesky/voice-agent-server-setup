#!/bin/bash
# STT Service Setup Script for RunPod
# This script installs and configures the STT service

set -e

echo "============================================"
echo "STT Service Setup for RunPod"
echo "============================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📍 Working directory: $SCRIPT_DIR${NC}"

# Check if running on RunPod
if [ -d "/workspace" ]; then
    echo -e "${GREEN}✅ Running on RunPod environment${NC}"
    WORKSPACE_DIR="/workspace/stt_service"
else
    echo -e "${YELLOW}⚠️  Not running on RunPod, using local installation${NC}"
    WORKSPACE_DIR="$SCRIPT_DIR"
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
echo -e "${YELLOW}🔍 Checking Python installation...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check pip
if ! command_exists pip3; then
    echo -e "${RED}❌ pip3 not found. Installing...${NC}"
    python3 -m ensurepip --upgrade
fi

# Check CUDA availability
echo -e "${YELLOW}🔍 Checking CUDA availability...${NC}"
if command_exists nvidia-smi; then
    nvidia-smi > /dev/null 2>&1 && echo -e "${GREEN}✅ CUDA available${NC}" || echo -e "${YELLOW}⚠️  CUDA not available, will use CPU${NC}"
else
    echo -e "${YELLOW}⚠️  nvidia-smi not found, will use CPU${NC}"
fi

# Install system dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
if command_exists apt-get; then
    sudo apt-get update > /dev/null 2>&1 || echo "Unable to update apt (might not have sudo)"
    sudo apt-get install -y ffmpeg libsndfile1 > /dev/null 2>&1 || echo "Installing ffmpeg and libsndfile1 (might need manual installation)"
elif command_exists yum; then
    sudo yum install -y ffmpeg libsndfile > /dev/null 2>&1 || echo "Installing dependencies with yum"
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p models
mkdir -p tmp

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip3 install --upgrade pip > /dev/null 2>&1

if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip3 install -r requirements.txt --no-cache-dir
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << 'EOF'
# STT Service Configuration

# Model Configuration
STT_MODEL_NAME=large-v3-turbo
STT_DEVICE=cuda
STT_COMPUTE_TYPE=int8

# Authentication
STT_API_KEY=stt_secret_key_production_123456

# VAD Configuration
STT_VAD_ENABLED=true
STT_VAD_THRESHOLD=0.5
STT_VAD_MIN_SPEECH_DURATION_MS=250
STT_VAD_MIN_SILENCE_DURATION_MS=200

# Service Limits
STT_MAX_FILE_SIZE_MB=100
STT_MAX_WEBSOCKET_CONNECTIONS=100
STT_REQUEST_TIMEOUT_SECONDS=300

# Server Configuration
STT_HOST=0.0.0.0
STT_PORT=8000
STT_WORKERS=1
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Make scripts executable
echo -e "${YELLOW}🔧 Setting script permissions...${NC}"
chmod +x start.sh stop.sh restart.sh status.sh 2>/dev/null || true

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review and edit .env file if needed"
echo "  2. Start the service: ./start.sh"
echo "  3. Check status: ./status.sh"
echo "  4. View logs: tail -f logs/stt_service.log"
echo ""

