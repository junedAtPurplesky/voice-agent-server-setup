#!/bin/bash
# Start STT Service

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}🚀 Starting STT Service...${NC}"

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✅ Loaded environment variables${NC}"
else
    echo -e "${YELLOW}⚠️  No .env file found, using defaults${NC}"
fi

# Check if service is already running
if [ -f "stt_service.pid" ]; then
    PID=$(cat stt_service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Service is already running (PID: $PID)${NC}"
        echo "Use ./restart.sh to restart or ./stop.sh to stop"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Removing stale PID file${NC}"
        rm stt_service.pid
    fi
fi

# Create logs directory
mkdir -p logs

# Start the service
echo -e "${YELLOW}📦 Starting uvicorn server...${NC}"

# Start service in background
nohup python3 -m uvicorn app.main:app \
    --host ${STT_HOST:-0.0.0.0} \
    --port ${STT_PORT:-8000} \
    --workers ${STT_WORKERS:-1} \
    --log-level info \
    > logs/stt_service.log 2>&1 &

# Save PID
echo $! > stt_service.pid

sleep 2

# Check if service started successfully
if ps -p $(cat stt_service.pid) > /dev/null 2>&1; then
    PID=$(cat stt_service.pid)
    echo -e "${GREEN}✅ STT Service started successfully!${NC}"
    echo "   PID: $PID"
    echo "   Host: ${STT_HOST:-0.0.0.0}"
    echo "   Port: ${STT_PORT:-8000}"
    echo ""
    echo "Service endpoints:"
    echo "   Health: http://localhost:${STT_PORT:-8000}/stt/health"
    echo "   API Docs: http://localhost:${STT_PORT:-8000}/stt/docs"
    echo ""
    echo "Logs: tail -f logs/stt_service.log"
else
    echo -e "${RED}❌ Failed to start service${NC}"
    echo "Check logs: cat logs/stt_service.log"
    rm -f stt_service.pid
    exit 1
fi

