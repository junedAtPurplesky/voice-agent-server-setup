#!/bin/bash
################################################################################
# Status of All Services
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/ports.conf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          Voice Agent Services Status                     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

check_service() {
    local name=$1
    local port=$2
    local pid_file="$PID_DIR/${name,,}.pid"
    
    printf "%-15s" "$name:"
    
    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        if curl -s -f "http://localhost:$port/health" --max-time 2 > /dev/null 2>&1; then
            echo -e "${GREEN}● RUNNING${NC}  (Port: $port, PID: $(cat $pid_file))"
        else
            echo -e "${YELLOW}◐ DEGRADED${NC} (Port: $port, health check failed)"
        fi
    else
        echo -e "${RED}○ STOPPED${NC}"
        [ -f "$pid_file" ] && rm -f "$pid_file"
    fi
}

check_service "STT" "$STT_PORT"
check_service "TTS" "$TTS_PORT"
check_service "LLM" "$LLM_PORT"

echo ""
