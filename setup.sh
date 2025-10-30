#!/bin/bash
################################################################################
# Voice Agent Server Setup - Production Installation
# RunPod RTX 3090: 24GB VRAM, 125GB RAM, 16 vCPU
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

clear
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                  ║${NC}"
echo -e "${CYAN}║        ${BOLD}Voice Agent Server Setup - Production v2.0${NC}${CYAN}          ║${NC}"
echo -e "${CYAN}║                                                                  ║${NC}"
echo -e "${CYAN}║  Platform: RunPod RTX 3090 | 24GB VRAM | 125GB RAM | 16 vCPU   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"
# Check GPU
if ! nvidia-smi &> /dev/null; then
    echo -e "${RED}❌ Error: NVIDIA GPU not detected${NC}"
    exit 1
fi
echo -e "${GREEN}✓ GPU detected:${NC}"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | head -1
echo ""

echo -e "${YELLOW}[2/8] Creating directory structure...${NC}"
mkdir -p "$BASE_DIR"/{bin,config,services/{stt_service,tts_service,llm_service}/app,scripts/{install,utils,debug},tests/{integration,performance,load},logs/{stt,tts,llm},pids,data/{models,temp},venv}
echo -e "${GREEN}✓ Directory structure created${NC}\n"

echo -e "${YELLOW}[3/8] Installing system dependencies...${NC}"
bash "$BASE_DIR/scripts/install/install-system-deps.sh"
echo ""

echo -e "${YELLOW}[4/8] Creating Python virtual environment...${NC}"
# Create or repair venv
if [ -d "$BASE_DIR/venv" ] && [ ! -f "$BASE_DIR/venv/bin/activate" ]; then
    echo -e "${YELLOW}Existing venv is malformed (missing bin/activate). Recreating...${NC}"
    rm -rf "$BASE_DIR/venv"
fi

if [ ! -d "$BASE_DIR/venv" ]; then
    if command -v python3.11 >/dev/null 2>&1; then
        python3.11 -m venv "$BASE_DIR/venv"
    else
        python3 -m venv "$BASE_DIR/venv"
    fi
fi

if [ ! -f "$BASE_DIR/venv/bin/activate" ]; then
    echo -e "${RED}❌ Error: Virtual environment creation failed (no bin/activate).${NC}"
    echo -e "${YELLOW}Hint:${NC} Ensure python venv is available (package: python3.11-venv)."
    exit 1
fi

source "$BASE_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel -q
echo -e "${GREEN}✓ Virtual environment ready${NC}\n"

echo -e "${YELLOW}[5/8] Installing Python dependencies with Poetry...${NC}"
# Install Poetry inside the project venv and configure to use current venv
pip install -q poetry
poetry config virtualenvs.create false || true

# Ensure CUDA 12.1 wheels for PyTorch
export PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cu121"

# Install all dependencies defined in pyproject.toml
poetry install --no-ansi --no-interaction

# Install CosyVoice directly via pip from git (project lacks pyproject/setup.py for Poetry)
echo -e "${YELLOW}Installing CosyVoice (git) via pip...${NC}"
pip install --no-cache-dir -q "git+https://github.com/FunAudioLLM/CosyVoice.git@main"
echo ""

echo -e "${YELLOW}[6/8] Applying CUDA optimizations...${NC}"
bash "$BASE_DIR/scripts/utils/optimize-cuda.sh"
echo ""

echo -e "${YELLOW}[7/8] Setting up service scripts...${NC}"
chmod +x "$BASE_DIR"/bin/*.sh
chmod +x "$BASE_DIR"/services/*/start.sh
chmod +x "$BASE_DIR"/services/*/stop.sh
chmod +x "$BASE_DIR"/scripts/*/*.sh
chmod +x "$BASE_DIR"/tests/*/*.sh
echo -e "${GREEN}✓ All scripts are executable${NC}\n"

echo -e "${YELLOW}[8/8] Verifying installation...${NC}"
bash "$BASE_DIR/scripts/utils/check-gpu.sh"

deactivate

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}║               ${BOLD}✓ Installation Complete!${NC}${GREEN}                          ║${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}${BOLD}Next Steps:${NC}"
echo -e "  ${YELLOW}1.${NC} Review configuration: ${BLUE}config/stt.env, config/tts.env, config/llm.env${NC}"
echo -e "  ${YELLOW}2.${NC} Start all services:   ${BLUE}./bin/start-all.sh${NC}"
echo -e "  ${YELLOW}3.${NC} Check health:         ${BLUE}./bin/health-check.sh${NC}"
echo -e "  ${YELLOW}4.${NC} Monitor system:       ${BLUE}./bin/monitor.sh${NC}\n"

echo -e "${CYAN}${BOLD}Individual Service Management:${NC}"
echo -e "  ${BLUE}./bin/start-stt.sh${NC}    ${BLUE}./bin/stop-stt.sh${NC}    ${BLUE}./bin/restart-stt.sh${NC}"
echo -e "  ${BLUE}./bin/start-tts.sh${NC}    ${BLUE}./bin/stop-tts.sh${NC}    ${BLUE}./bin/restart-tts.sh${NC}"
echo -e "  ${BLUE}./bin/start-llm.sh${NC}    ${BLUE}./bin/stop-llm.sh${NC}    ${BLUE}./bin/restart-llm.sh${NC}\n"

echo -e "${CYAN}${BOLD}Debug Model Loading:${NC}"
echo -e "  ${BLUE}python scripts/debug/test-stt-model.py${NC}"
echo -e "  ${BLUE}python scripts/debug/test-tts-model.py${NC}"
echo -e "  ${BLUE}python scripts/debug/test-llm-model.py${NC}\n"
