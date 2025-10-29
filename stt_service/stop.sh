#!/bin/bash
# Stop STT Service

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}🛑 Stopping STT Service...${NC}"

if [ ! -f "stt_service.pid" ]; then
    echo -e "${RED}❌ No PID file found. Service might not be running.${NC}"
    exit 1
fi

PID=$(cat stt_service.pid)

if ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}Stopping process $PID...${NC}"
    kill $PID
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Force killing process...${NC}"
        kill -9 $PID
    fi
    
    echo -e "${GREEN}✅ Service stopped successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Process $PID not found (might have crashed)${NC}"
fi

rm -f stt_service.pid

