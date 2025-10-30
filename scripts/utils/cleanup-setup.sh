#!/bin/bash
################################################################################
# Cleanup project artifacts from an older setup run (idempotent)
# - Removes project venv
# - Removes CosyVoice clone and any .pth linker
# - Purges pip cache within current Python context
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${YELLOW}Cleaning up old setup artifacts in:${NC} ${BLUE}${BASE_DIR}${NC}\n"

# 1) Deactivate any active venv
if command -v deactivate >/dev/null 2>&1; then
    deactivate || true
fi

# 2) Remove project venv
if [ -d "${BASE_DIR}/venv" ]; then
    echo -e "${YELLOW}- Removing venv...${NC}"
    rm -rf "${BASE_DIR}/venv"
    echo -e "${GREEN}  ✓ venv removed${NC}"
else
    echo -e "${GREEN}  ✓ No venv found (skipped)${NC}"
fi

# 3) Remove CosyVoice clone
if [ -d "${BASE_DIR}/data/models/CosyVoice" ]; then
    echo -e "${YELLOW}- Removing CosyVoice clone...${NC}"
    rm -rf "${BASE_DIR}/data/models/CosyVoice"
    echo -e "${GREEN}  ✓ CosyVoice removed${NC}"
else
    echo -e "${GREEN}  ✓ No CosyVoice clone found (skipped)${NC}"
fi

# 4) Remove .pth linker(s) created by setup
remove_pth() {
    local py_bin="$1"
    if command -v "$py_bin" >/dev/null 2>&1; then
        local site
        site="$($py_bin - <<'PY'
import sysconfig
print(sysconfig.get_paths().get('purelib',''))
PY
)"
        if [ -n "$site" ] && [ -d "$site" ]; then
            if [ -f "$site/cosyvoice_src.pth" ]; then
                echo -e "${YELLOW}- Removing $py_bin site .pth at:${NC} ${site}/cosyvoice_src.pth"
                rm -f "$site/cosyvoice_src.pth"
                echo -e "${GREEN}  ✓ .pth removed${NC}"
            fi
        fi
    fi
}

remove_pth python3.11 || true
remove_pth python3 || true

# 5) Purge pip cache (safe)
if command -v pip >/dev/null 2>&1; then
    echo -e "${YELLOW}- Purging pip cache...${NC}"
    pip cache purge >/dev/null 2>&1 || true
    echo -e "${GREEN}  ✓ Pip cache purged${NC}"
else
    echo -e "${GREEN}  ✓ No pip found (skipped cache purge)${NC}"
fi

echo -e "\n${GREEN}Cleanup complete.${NC}"


