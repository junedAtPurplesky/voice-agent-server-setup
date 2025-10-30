#!/bin/bash
################################################################################
# Comprehensive Health Check
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

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          Voice Agent Health Check Report                        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

# System Resources
echo -e "${BLUE}═══ System Resources ═══${NC}\n"

echo -e "${YELLOW}GPU Status:${NC}"
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
while IFS=',' read -r idx name temp gpu_util mem_used mem_total; do
    mem_percent=$((mem_used * 100 / mem_total))
    echo -e "  GPU $idx: $name"
    echo -e "    Temp: ${temp}°C | GPU: ${gpu_util}% | VRAM: ${mem_used}MB/${mem_total}MB (${mem_percent}%)"
done

echo -e "\n${YELLOW}CPU & Memory:${NC}"
cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
mem_info=$(free -h | awk '/^Mem:/ {print $3 " / " $2 " (" int($3/$2 * 100) "%)"}')
echo -e "  CPU: ${cpu_usage}%"
echo -e "  Memory: $mem_info"

# Service Health Checks
echo -e "\n${BLUE}═══ Service Health Checks ═══${NC}\n"

check_service() {
    local name=$1
    local port=$2
    local endpoint="/health"
    
    echo -e "${YELLOW}$name (Port $port):${NC}"
    
    if ! nc -z localhost $port 2>/dev/null; then
        echo -e "  ${RED}✗ Not responding on port $port${NC}\n"
        return 1
    fi
    
    response=$(curl -s -w "\n%{http_code}" "http://localhost:$port$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" == "200" ]; then
        echo -e "  ${GREEN}✓ HTTP Status: 200 OK${NC}"
        
        if command -v jq &> /dev/null && echo "$body" | jq . > /dev/null 2>&1; then
            status=$(echo "$body" | jq -r '.status // "unknown"')
            model=$(echo "$body" | jq -r '.model // .service // "N/A"')
            echo -e "  ${GREEN}✓ Status: $status${NC}"
            echo -e "  ${GREEN}✓ Model: $model${NC}"
        fi
        
        response_time=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:$port$endpoint")
        echo -e "  ${GREEN}✓ Response Time: ${response_time}s${NC}"
        echo ""
        return 0
    else
        echo -e "  ${RED}✗ HTTP Status: $http_code${NC}\n"
        return 1
    fi
}

stt_status=0
tts_status=0
llm_status=0

check_service "STT Service" "$STT_PORT" || stt_status=1
check_service "TTS Service" "$TTS_PORT" || tts_status=1
check_service "LLM Service" "$LLM_PORT" || llm_status=1

# Overall Status
echo -e "${BLUE}═══ Overall Status ═══${NC}"
total_healthy=$((3 - stt_status - tts_status - llm_status))

if [ $total_healthy -eq 3 ]; then
    echo -e "${GREEN}✓ All services healthy ($total_healthy/3)${NC}\n"
    exit 0
elif [ $total_healthy -gt 0 ]; then
    echo -e "${YELLOW}⚠ Partial health ($total_healthy/3 services healthy)${NC}\n"
    exit 1
else
    echo -e "${RED}✗ All services down (0/3)${NC}\n"
    exit 2
fi
