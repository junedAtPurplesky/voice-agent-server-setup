#!/bin/bash
# Restart STT Service

set -e

# Colors
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}🔄 Restarting STT Service...${NC}"

./stop.sh 2>/dev/null || true
sleep 2
./start.sh

