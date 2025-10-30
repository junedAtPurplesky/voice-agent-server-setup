#!/bin/bash
################################################################################
# Start TTS Service (Text-to-Speech)
################################################################################

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/tts.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_FILE="$PID_DIR/tts.pid"
LOG_FILE="$LOG_DIR/tts/tts_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Starting TTS Service (CosyVoice2)             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}\n"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠ TTS service already running (PID: $OLD_PID)${NC}"
        echo -e "${YELLOW}  Use ./bin/stop-tts.sh to stop it first${NC}"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Export environment
export TTS_API_KEY
export TTS_SERVICE_PORT
export TTS_MODEL_NAME
export TTS_DEVICE

echo -e "${BLUE}→ Configuration:${NC}"
echo -e "  Model: ${GREEN}$TTS_MODEL_NAME${NC}"
echo -e "  Port:  ${GREEN}$TTS_SERVICE_PORT${NC}"
echo -e "  Device: ${GREEN}$TTS_DEVICE${NC}\n"

echo -e "${BLUE}→ Starting service...${NC}"

# Start service
nohup python "$BASE_DIR/services/tts_service/app/tts_main.py" > "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# Wait for initialization
echo -e "${BLUE}→ Initializing (this may take 20-30 seconds)...${NC}"
sleep 5

# Verify process is running
if ! kill -0 $PID 2>/dev/null; then
    echo -e "${RED}✗ Failed to start TTS service${NC}"
    echo -e "${RED}  Check logs: tail -f $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

# Wait for health check
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:$TTS_SERVICE_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ TTS service started successfully!${NC}"
        echo -e "${GREEN}  PID: $PID${NC}"
        echo -e "${GREEN}  Port: $TTS_SERVICE_PORT${NC}"
        echo -e "${GREEN}  URL: http://$(hostname -I | awk '{print $1}'):$TTS_SERVICE_PORT${NC}"
        echo -e "${GREEN}  Logs: $LOG_FILE${NC}\n"
        
        # Show endpoints
        echo -e "${BLUE}Available Endpoints:${NC}"
        echo -e "  ${YELLOW}POST${NC} /synthesize - Synthesize speech"
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
