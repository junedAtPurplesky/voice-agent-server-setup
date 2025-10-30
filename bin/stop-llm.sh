#!/bin/bash
################################################################################
# Stop LLM Service
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$BASE_DIR/config/system.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_FILE="$PID_DIR/llm.pid"

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Stopping LLM Service                           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}\n"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠ LLM service is not running${NC}"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo -e "${YELLOW}⚠ LLM service (PID: $PID) is not running${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

echo -e "${BLUE}→ Stopping LLM service (PID: $PID)...${NC}"
kill -TERM "$PID" 2>/dev/null

TIMEOUT=15
while kill -0 "$PID" 2>/dev/null && [ $TIMEOUT -gt 0 ]; do
    sleep 1
    TIMEOUT=$((TIMEOUT - 1))
    echo -n "."
done
echo ""

if kill -0 "$PID" 2>/dev/null; then
    echo -e "${YELLOW}→ Force killing...${NC}"
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi

rm -f "$PID_FILE"
echo -e "${GREEN}✓ LLM service stopped${NC}\n"
