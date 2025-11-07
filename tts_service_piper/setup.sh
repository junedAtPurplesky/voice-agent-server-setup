#!/bin/bash

set -e

echo "=========================================="
echo "Piper TTS Service Setup"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "Step 1: Setting up Python virtual environment..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    echo "Please install Python 3.8 or later"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "Found Python version: $PYTHON_VERSION"

# Create virtual environment
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing and recreating..."
    rm -rf venv
fi

echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "✓ Virtual environment created and activated"
echo "  Python: $(which python)"
echo "  Python version: $(python --version)"

echo ""
echo "Step 2: Installing Python dependencies..."
echo ""

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "✓ Dependencies installed successfully"

echo ""
echo "Step 3: Setting up Piper models directory..."
echo ""

# Create models directory
mkdir -p piper_models

echo "✓ Models directory created: $SCRIPT_DIR/piper_models"

echo ""
echo "Step 4: Downloading default voice models..."
echo ""

# Function to download voice model
download_model() {
    local voice_id=$1
    local base_url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
    
    # Determine language and path
    if [[ $voice_id == en_* ]]; then
        lang="en"
        if [[ $voice_id == en_US* ]]; then
            region="us"
        elif [[ $voice_id == en_GB* ]]; then
            region="gb"
        fi
    elif [[ $voice_id == hi_* ]]; then
        lang="hi"
        region="in"
    fi
    
    local model_file="${voice_id}.onnx"
    local config_file="${voice_id}.onnx.json"
    
    echo "Downloading ${voice_id}..."
    
    # Construct URLs
    local model_url="${base_url}/${lang}/${region}/${voice_id}/${model_file}"
    local config_url="${base_url}/${lang}/${region}/${voice_id}/${config_file}"
    
    # Download model
    if [ ! -f "piper_models/${model_file}" ]; then
        curl -L -o "piper_models/${model_file}" "$model_url" 2>/dev/null || {
            echo "  ⚠ Failed to download model (will be downloaded on first use)"
            return 1
        }
        echo "  ✓ Model downloaded"
    else
        echo "  ✓ Model already exists"
    fi
    
    # Download config
    if [ ! -f "piper_models/${config_file}" ]; then
        curl -L -o "piper_models/${config_file}" "$config_url" 2>/dev/null || {
            echo "  ⚠ Failed to download config (will be downloaded on first use)"
            return 1
        }
        echo "  ✓ Config downloaded"
    else
        echo "  ✓ Config already exists"
    fi
    
    return 0
}

# Download default English voice
echo "English voice (Lessac - US):"
download_model "en_US-lessac-medium" || echo "  Note: Model will auto-download on first use"

echo ""
echo "Hindi voice (Madhur - India):"
download_model "hi_IN-madhur-medium" || echo "  Note: Model will auto-download on first use"

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Piper TTS service is ready to use."
echo ""
echo "Available voices:"
echo "  English:"
echo "    - en_US-lessac-medium (US Male)"
echo "    - en_US-amy-medium (US Female)"
echo "    - en_GB-alan-medium (GB Male)"
echo ""
echo "  Hindi:"
echo "    - hi_IN-madhur-medium (India Male)"
echo "    - hi_IN-female-medium (India Female)"
echo ""
echo "Note: Voice models will be automatically downloaded"
echo "      on first use if not present."
echo ""
echo "Next steps:"
echo "  1. Start service: ./start_service.sh"
echo "  2. Check status:  ./tts_manager.sh status"
echo "  3. Test service:  python test_client.py"
echo ""
echo "Service will run on: http://localhost:8003"
echo ""

