#!/bin/bash
# Check STT Service Status

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================"
echo "STT Service Status"
echo "============================================"

if [ -f "stt_service.pid" ]; then
    PID=$(cat stt_service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is running${NC}"
        echo "   PID: $PID"
        
        # Get process info
        echo "   Memory: $(ps -o rss= -p $PID | awk '{printf "%.2f MB", $1/1024}')"
        echo "   CPU: $(ps -o %cpu= -p $PID)%"
        echo "   Start time: $(ps -o lstart= -p $PID)"
        
        # Check if port is listening
        PORT=${STT_PORT:-8000}
        if command -v netstat > /dev/null 2>&1; then
            if netstat -tuln 2>/dev/null | grep -q ":$PORT"; then
                echo -e "   Port $PORT: ${GREEN}Listening${NC}"
            fi
        elif command -v ss > /dev/null 2>&1; then
            if ss -tuln 2>/dev/null | grep -q ":$PORT"; then
                echo -e "   Port $PORT: ${GREEN}Listening${NC}"
            fi
        fi
        
        # Try health check
        echo ""
        echo "Health check:"
        if command -v curl > /dev/null 2>&1; then
            curl -s http://localhost:$PORT/stt/health | python3 -m json.tool 2>/dev/null || echo "Service not responding"
        else
            echo "curl not available for health check"
        fi
    else
        echo -e "${RED}❌ Service is not running (stale PID file)${NC}"
        rm -f stt_service.pid
    fi
else
    echo -e "${RED}❌ Service is not running${NC}"
fi

echo ""
echo "Recent logs (last 10 lines):"
echo "-------------------------------------------"
if [ -f "logs/stt_service.log" ]; then
    tail -n 10 logs/stt_service.log
else
    echo "No log file found"
fi

