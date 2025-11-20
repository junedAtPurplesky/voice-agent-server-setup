#!/usr/bin/env bash
# ==========================================================
# Test Environment Setup
# Automatically creates venv and installs dependencies
# ==========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.test_venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

setup_venv() {
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Creating virtual environment for testing...${NC}"
    python3 -m venv "$VENV_DIR"
    
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
    
    echo -e "${GREEN}✓ Test environment ready${NC}"
}

# Setup if needed
setup_venv

# Activate venv
source "$VENV_DIR/bin/activate"

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo "Python: $(which python3)"
echo "You can now run: python3 test_client.py"

