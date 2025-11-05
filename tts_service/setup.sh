#!/bin/bash

set -e

echo "=========================================="
echo "CosyVoice TTS Service Setup (Official)"
echo "Following: github.com/FunAudioLLM/CosyVoice"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if conda is installed, install if not
echo ""
echo "Step 1: Checking Conda installation..."

# Check if conda command is available
if ! command -v conda &> /dev/null; then
    # Conda command not found, check if it's installed but not in PATH
    if [ -d "$HOME/miniconda3" ]; then
        echo "Miniconda installation found at $HOME/miniconda3 but not in PATH."
        echo "Adding to PATH and initializing..."
        
        # Add to PATH for this script
        export PATH="$HOME/miniconda3/bin:$PATH"
        
        # Initialize conda for bash
        "$HOME/miniconda3/bin/conda" init bash 2>/dev/null || true
        
        # Source conda setup for this script
        if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
            source "$HOME/miniconda3/etc/profile.d/conda.sh"
        fi
        
        echo "✓ Conda activated from existing installation"
        echo "  Location: $HOME/miniconda3"
        echo "  Version: $(conda --version)"
        echo ""
        
    else
        # No installation found, install fresh
        echo "Conda is not installed. Installing Miniconda automatically..."
        echo ""
        
        # Detect OS and architecture
        OS_TYPE=$(uname -s)
        ARCH_TYPE=$(uname -m)
        
        # Determine download URL based on OS and architecture
        if [ "$OS_TYPE" = "Linux" ]; then
            if [ "$ARCH_TYPE" = "x86_64" ]; then
                MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            elif [ "$ARCH_TYPE" = "aarch64" ]; then
                MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
            else
                echo "ERROR: Unsupported Linux architecture: $ARCH_TYPE"
                exit 1
            fi
        elif [ "$OS_TYPE" = "Darwin" ]; then
            if [ "$ARCH_TYPE" = "x86_64" ]; then
                MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
            elif [ "$ARCH_TYPE" = "arm64" ]; then
                MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
            else
                echo "ERROR: Unsupported macOS architecture: $ARCH_TYPE"
                exit 1
            fi
        else
            echo "ERROR: Unsupported operating system: $OS_TYPE"
            echo "Please install Conda manually: https://docs.conda.io/en/latest/miniconda.html"
            exit 1
        fi
        
        echo "Detected: $OS_TYPE on $ARCH_TYPE"
        echo "Downloading Miniconda installer..."
        
        # Download installer
        INSTALLER_PATH="/tmp/miniconda_installer.sh"
        if command -v wget &> /dev/null; then
            wget -q --show-progress "$MINICONDA_URL" -O "$INSTALLER_PATH"
        elif command -v curl &> /dev/null; then
            curl -L "$MINICONDA_URL" -o "$INSTALLER_PATH"
        else
            echo "ERROR: Neither wget nor curl is available. Please install one of them."
            exit 1
        fi
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to download Miniconda installer"
            exit 1
        fi
        
        echo "Installing Miniconda..."
        echo "This will install to: $HOME/miniconda3"
        
        # Install Miniconda in batch mode (no prompts)
        bash "$INSTALLER_PATH" -b -p "$HOME/miniconda3"
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Miniconda installation failed"
            rm -f "$INSTALLER_PATH"
            exit 1
        fi
        
        # Clean up installer
        rm -f "$INSTALLER_PATH"
        
        # Initialize conda for the current shell
        "$HOME/miniconda3/bin/conda" init bash
        
        # Source conda for this script
        export PATH="$HOME/miniconda3/bin:$PATH"
        
        # Source conda setup
        if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
            source "$HOME/miniconda3/etc/profile.d/conda.sh"
        fi
        
        echo "✓ Miniconda installed successfully"
        echo ""
        echo "NOTE: You may need to restart your shell after this script completes"
        echo "      for conda to be available in future terminal sessions."
        echo ""
    fi
else
    echo "✓ Conda found: $(conda --version)"
fi

# Install system dependencies
echo ""
echo "Step 2: Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Installing system packages (Ubuntu/Debian)..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        git \
        git-lfs \
        ffmpeg \
        libsndfile1 \
        sox
    echo "✓ System dependencies installed"
elif command -v yum &> /dev/null; then
    echo "Installing system packages (CentOS/RHEL)..."
    sudo yum install -y git git-lfs ffmpeg libsndfile sox
    echo "✓ System dependencies installed"
elif command -v brew &> /dev/null; then
    echo "Installing system packages (macOS)..."
    brew install git git-lfs ffmpeg libsndfile sox
    echo "✓ System dependencies installed"
else
    echo "⚠ Warning: Could not detect package manager"
    echo "Please ensure these are installed: git, git-lfs, ffmpeg, libsndfile, sox"
fi

# Initialize git-lfs
echo ""
echo "Step 3: Initializing Git LFS..."
git lfs install
echo "✓ Git LFS initialized"

# Configure Conda settings
echo ""
echo "Step 4: Configuring Conda..."
echo "Accepting Conda Terms of Service..."

# Get conda base path first
CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")

# Accept Anaconda Terms of Service (required for newer Conda versions)
conda config --set allow_conda_downgrades true 2>/dev/null || true
conda config --set channel_priority flexible 2>/dev/null || true
conda config --set safety_checks warn 2>/dev/null || true
conda config --set restore_free_channel true 2>/dev/null || true

# Explicitly accept TOS for Anaconda channels (required for non-interactive setup)
echo "Accepting Terms of Service for Anaconda channels..."
conda config --set auto_update_conda false 2>/dev/null || true

# Try to accept TOS using conda tos command
# Check if conda tos command exists (newer conda versions)
if conda --help | grep -q "tos"; then
    echo "  Accepting TOS for pkgs/main channel..."
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
    echo "  Accepting TOS for pkgs/r channel..."
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true
else
    echo "  (conda tos command not available - using older conda version)"
fi

echo "✓ Conda configured"

# Create or update conda environment
echo ""
echo "Step 5: Setting up Conda environment..."
ENV_NAME="cosyvoice"

if conda env list | grep -q "^${ENV_NAME} "; then
    echo "Conda environment '${ENV_NAME}' already exists."
    echo "Using existing environment..."
else
    echo "Creating conda environment '${ENV_NAME}' with Python 3.8..."
    # Use conda-forge and defaults channels with explicit channel priority
    conda create -n ${ENV_NAME} python=3.8 -c conda-forge -c defaults -y
fi

echo "✓ Conda environment ready"

# Get conda base path
CONDA_BASE=$(conda info --base)
echo ""
echo "Activating conda environment..."
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate ${ENV_NAME}

echo "✓ Environment activated: $(which python)"
echo "  Python version: $(python --version)"

# Install PyTorch with CUDA support if available
echo ""
echo "Step 6: Installing PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing PyTorch with CUDA 11.8..."
    pip install torch==2.0.1 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
else
    echo "No NVIDIA GPU detected. Installing CPU version..."
    pip install torch==2.0.1 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
fi

echo "✓ PyTorch installed"
python -c "import torch; print(f'  PyTorch: {torch.__version__}'); print(f'  CUDA available: {torch.cuda.is_available()}')"

# Clone or update CosyVoice repository
echo ""
echo "Step 7: Setting up CosyVoice repository..."
if [ -d "CosyVoice" ]; then
    echo "CosyVoice directory exists. Updating..."
    cd CosyVoice
    git pull
    git submodule update --init --recursive
    cd ..
else
    echo "Cloning CosyVoice repository..."
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to clone CosyVoice repository"
        exit 1
    fi
fi

echo "✓ CosyVoice repository ready"

# Install CosyVoice dependencies (official requirements)
echo ""
echo "Step 8: Installing CosyVoice dependencies..."
cd CosyVoice

# Install from official requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing from official requirements.txt..."
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found in CosyVoice directory"
    exit 1
fi

cd ..
echo "✓ CosyVoice dependencies installed"

# Install service-specific dependencies
echo ""
echo "Step 9: Installing service dependencies..."
cat > requirements_service.txt << 'EOF'
# FastAPI and web server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0

# Pydantic for config
pydantic==2.5.3

# Additional utilities
requests==2.31.0
EOF

pip install -r requirements_service.txt
rm requirements_service.txt

echo "✓ Service dependencies installed"

# Setup Python path for imports
echo ""
echo "Step 10: Configuring Python imports..."
COSYVOICE_PATH="${SCRIPT_DIR}/CosyVoice"
THIRD_PARTY_PATH="${COSYVOICE_PATH}/third_party/Matcha-TTS"

# Create sitecustomize.py to add paths automatically
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
cat > "${SITE_PACKAGES}/sitecustomize.py" << EOF
import sys
import os

# Add CosyVoice to path
cosyvoice_path = "${COSYVOICE_PATH}"
if cosyvoice_path not in sys.path:
    sys.path.insert(0, cosyvoice_path)

# Add Matcha-TTS to path
matcha_path = "${THIRD_PARTY_PATH}"
if matcha_path not in sys.path:
    sys.path.insert(0, matcha_path)
EOF

echo "✓ Python paths configured"
echo "  CosyVoice path: ${COSYVOICE_PATH}"
echo "  Matcha-TTS path: ${THIRD_PARTY_PATH}"

# Download pretrained models
echo ""
echo "Step 11: Setting up model configuration..."
mkdir -p pretrained_models

cat > .cosyvoice_config << 'EOF'
# CosyVoice Model Configuration
# Models will be downloaded automatically from ModelScope on first use

# Available models:
# - CosyVoice-300M: Base model
# - CosyVoice-300M-SFT: SFT model (recommended)
# - CosyVoice-300M-Instruct: Instruct model
# - CosyVoice2-0.5B: Latest model (smaller, faster)

# Default model for service
MODEL_DIR="pretrained_models/CosyVoice-300M-SFT"
EOF

echo "✓ Model configuration created"
echo ""
echo "Note: Models will be downloaded automatically from ModelScope on first use."
echo "You can also manually download models using:"
echo "  cd CosyVoice"
echo "  python -c \"from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')\""

# Create activation helper script
echo ""
echo "Step 12: Creating helper scripts..."

cat > activate_env.sh << 'EOF'
#!/bin/bash
# Helper script to activate the cosyvoice environment
CONDA_BASE=$(conda info --base)
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate cosyvoice
echo "✓ Conda environment 'cosyvoice' activated"
echo "  Python: $(which python)"
echo "  Python version: $(python --version)"
EOF
chmod +x activate_env.sh

echo "✓ Helper scripts created"

# Test installation
echo ""
echo "Step 13: Testing installation..."
python << 'PYTEST'
import sys
import torch
import torchaudio

print("=" * 60)
print("Testing Core Dependencies")
print("=" * 60)
print(f"✓ Python: {sys.version}")
print(f"✓ PyTorch: {torch.__version__}")
print(f"✓ TorchAudio: {torchaudio.__version__}")
print(f"✓ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  - CUDA version: {torch.version.cuda}")
    print(f"  - GPU count: {torch.cuda.device_count()}")
    print(f"  - GPU name: {torch.cuda.get_device_name(0)}")

print("\nTesting CosyVoice Import")
print("=" * 60)
try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    from cosyvoice.utils.file_utils import load_wav
    print("✓ CosyVoice imports successful")
except ImportError as e:
    print(f"✗ CosyVoice import failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Make sure you're in the cosyvoice conda environment")
    print("  2. Check that CosyVoice directory exists")
    print("  3. Try: source activate_env.sh")
    sys.exit(1)

print("\nTesting FastAPI")
print("=" * 60)
try:
    import fastapi
    import uvicorn
    print(f"✓ FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
PYTEST

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Installation test failed!"
    echo "Please check the errors above."
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ SETUP COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "  1. Activate environment: source activate_env.sh"
echo "  2. Start service: ./start_service.sh"
echo "  3. Test service: python test_client.py"
echo ""
echo "Models will be downloaded automatically from ModelScope on first use."
echo "First startup may take several minutes while downloading models."
echo ""
echo "For manual model download:"
echo "  source activate_env.sh"
echo "  cd CosyVoice"
echo "  # For SFT model (recommended):"
echo "  python -c \"from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M-SFT', local_dir='../pretrained_models/CosyVoice-300M-SFT')\""
echo ""
