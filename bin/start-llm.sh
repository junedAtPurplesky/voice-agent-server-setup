#!/bin/bash
################################################################################
# Start LLM Service (Language Model)
################################################################################

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/llm.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PID_FILE="$PID_DIR/llm.pid"
LOG_FILE="$LOG_DIR/llm/llm_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Starting LLM Service (Qwen 2.5 7B AWQ)        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}\n"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠ LLM service already running (PID: $OLD_PID)${NC}"
        echo -e "${YELLOW}  Use ./bin/stop-llm.sh to stop it first${NC}"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Export environment
export LLM_API_KEY
export LLM_SERVICE_PORT
export LLM_MODEL_NAME
export LLM_QUANTIZATION
export LLM_DTYPE
export LLM_DEVICE
export LLM_MAX_MODEL_LEN
export LLM_GPU_MEMORY_UTILIZATION

echo -e "${BLUE}→ Configuration:${NC}"
echo -e "  Model: ${GREEN}$LLM_MODEL_NAME${NC}"
echo -e "  Quantization: ${GREEN}$LLM_QUANTIZATION (4-bit)${NC}"
echo -e "  Data Type: ${GREEN}$LLM_DTYPE${NC}"
echo -e "  Port:  ${GREEN}$LLM_SERVICE_PORT${NC}"
echo -e "  Device: ${GREEN}$LLM_DEVICE${NC}"
echo -e "  Max Length: ${GREEN}$LLM_MAX_MODEL_LEN${NC}"
echo -e "  GPU Memory: ${GREEN}${LLM_GPU_MEMORY_UTILIZATION}${NC}\n"

echo -e "${BLUE}→ Starting service...${NC}"

# Start service
nohup python "$BASE_DIR/services/llm_service/app/llm_main.py" > "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# Wait for initialization (LLM takes longer)
echo -e "${BLUE}→ Initializing (this may take 60-90 seconds for model loading)...${NC}"
sleep 10

# Verify process is running
if ! kill -0 $PID 2>/dev/null; then
    echo -e "${RED}✗ Failed to start LLM service${NC}"
    echo -e "${RED}  Check logs: tail -f $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

# Wait for health check
MAX_RETRIES=60
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:$LLM_SERVICE_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ LLM service started successfully!${NC}"
        echo -e "${GREEN}  PID: $PID${NC}"
        echo -e "${GREEN}  Port: $LLM_SERVICE_PORT${NC}"
        echo -e "${GREEN}  URL: http://$(hostname -I | awk '{print $1}'):$LLM_SERVICE_PORT${NC}"
        echo -e "${GREEN}  Logs: $LOG_FILE${NC}\n"
        
        # Show endpoints
        echo -e "${BLUE}Available Endpoints:${NC}"
        echo -e "  ${YELLOW}POST${NC} /v1/chat/completions - Chat completion (OpenAI compatible)"
        echo -e "  ${YELLOW}WS${NC}   /ws                 - WebSocket streaming"
        echo -e "  ${YELLOW}GET${NC}  /health             - Health check"
        echo -e "  ${YELLOW}GET${NC}  /docs               - API documentation\n"
        
        # Show VRAM usage
        vram_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
        echo -e "${BLUE}GPU Memory Usage: ${GREEN}${vram_used}MB${NC} (Expected: 3-4GB with AWQ)\n"
        
        exit 0
    fi
    RETRY=$((RETRY + 1))
    sleep 2
    if [ $((RETRY % 10)) -eq 0 ]; then
        echo -e "${YELLOW}  Still loading model... ($RETRY/$MAX_RETRIES)${NC}"
    fi
done

echo -e "\n${YELLOW}⚠ Service started but health check timed out${NC}"
echo -e "${YELLOW}  Check logs: tail -f $LOG_FILE${NC}"
exit 1
