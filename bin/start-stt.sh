#!/bin/bash
################################################################################
# Start STT Service (Speech-to-Text)
################################################################################

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/stt.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_FILE="$PID_DIR/stt.pid"
LOG_FILE="$LOG_DIR/stt/stt_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Starting STT Service (Faster Whisper)         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}\n"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠ STT service already running (PID: $OLD_PID)${NC}"
        echo -e "${YELLOW}  Use ./bin/stop-stt.sh to stop it first${NC}"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Export environment
export STT_API_KEY
export STT_SERVICE_PORT
export STT_MODEL_NAME
export STT_COMPUTE_TYPE
export STT_DEVICE

echo -e "${BLUE}→ Configuration:${NC}"
echo -e "  Model: ${GREEN}$STT_MODEL_NAME${NC}"
echo -e "  Port:  ${GREEN}$STT_SERVICE_PORT${NC}"
echo -e "  Device: ${GREEN}$STT_DEVICE${NC}"
echo -e "  Compute Type: ${GREEN}$STT_COMPUTE_TYPE${NC}\n"

echo -e "${BLUE}→ Starting service...${NC}"

# Start service
nohup python "$BASE_DIR/services/stt_service/app/stt_main.py" > "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# Wait for initialization
echo -e "${BLUE}→ Initializing (this may take 20-30 seconds)...${NC}"
sleep 5

# Verify process is running
if ! kill -0 $PID 2>/dev/null; then
    echo -e "${RED}✗ Failed to start STT service${NC}"
    echo -e "${RED}  Check logs: tail -f $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

# Wait for health check
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:$STT_SERVICE_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ STT service started successfully!${NC}"
        echo -e "${GREEN}  PID: $PID${NC}"
        echo -e "${GREEN}  Port: $STT_SERVICE_PORT${NC}"
        echo -e "${GREEN}  URL: http://$(hostname -I | awk '{print $1}'):$STT_SERVICE_PORT${NC}"
        echo -e "${GREEN}  Logs: $LOG_FILE${NC}\n"
        
        # Show endpoints
        echo -e "${BLUE}Available Endpoints:${NC}"
        echo -e "  ${YELLOW}POST${NC} /transcribe - Transcribe audio file"
        echo -e "  ${YELLOW}WS${NC}   /ws         - WebSocket streaming"
        echo -e "  ${YELLOW}GET${NC}  /health     - Health check"
        echo -e "  ${YELLOW}GET${NC}  /docs       - API documentation\n"
        
        exit 0
    fi
    RETRY=$((RETRY + 1))
    sleep 2
    echo -n "."
done

echo -e "\n${YELLOW}⚠ Service started but health check timed out${NC}"
echo -e "${YELLOW}  Check logs: tail -f $LOG_FILE${NC}"
exit 1
