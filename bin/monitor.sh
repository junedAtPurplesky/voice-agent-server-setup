#!/bin/bash
################################################################################
# Real-Time Service Monitor
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
BOLD='\033[1m'
NC='\033[0m'

while true; do
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       ${BOLD}Voice Agent Real-Time Monitor${NC}${CYAN} - $(date +"%Y-%m-%d %H:%M:%S")          ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
    
    # GPU Status
    echo -e "${BLUE}┌─ GPU Status ────────────────────────────────────────────────────────┐${NC}"
    nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits | \
    while IFS=',' read -r name temp gpu_util mem_used mem_total power; do
        mem_percent=$((mem_used * 100 / mem_total))
        echo -e "  ${YELLOW}GPU:${NC} $name"
        echo -e "  ${GREEN}Temp:${NC} ${temp}°C  ${GREEN}GPU:${NC} ${gpu_util}%  ${GREEN}VRAM:${NC} ${mem_used}/${mem_total}MB (${mem_percent}%)  ${GREEN}Power:${NC} ${power}W"
    done
    echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────┘${NC}\n"
    
    # System Resources
    echo -e "${BLUE}┌─ System Resources ──────────────────────────────────────────────────┐${NC}"
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    mem_info=$(free | awk '/^Mem:/ {printf "%.1fGB / %.1fGB (%.0f%%)", $3/1024/1024, $2/1024/1024, $3/$2 * 100}')
    load=$(uptime | awk -F'load average:' '{print $2}' | xargs)
    echo -e "  ${GREEN}CPU:${NC} ${cpu_usage}%  ${GREEN}Memory:${NC} $mem_info"
    echo -e "  ${GREEN}Load Average:${NC} $load"
    echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────┘${NC}\n"
    
    # Service Status
    echo -e "${BLUE}┌─ Service Status ────────────────────────────────────────────────────┐${NC}"
    
    check_service() {
        local name=$1
        local port=$2
        local pid_file="$PID_DIR/${name,,}.pid"
        
        printf "  %-20s" "$name:"
        
        if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
            if curl -s -f "http://localhost:$port/health" --max-time 2 > /dev/null 2>&1; then
                echo -e "${GREEN}● RUNNING${NC}  Port: $port  PID: $(cat $pid_file)"
            else
                echo -e "${YELLOW}◐ DEGRADED${NC} Port: $port (health check failed)"
            fi
        else
            echo -e "${RED}○ STOPPED${NC}"
        fi
    }
    
    check_service "STT" "$STT_PORT"
    check_service "TTS" "$TTS_PORT"
    check_service "LLM" "$LLM_PORT"
    echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────┘${NC}\n"
    
    # Recent Logs
    echo -e "${BLUE}┌─ Recent Activity ───────────────────────────────────────────────────┐${NC}"
    for service in stt tts llm; do
        log_file=$(ls -t "$LOG_DIR/$service"/*.log 2>/dev/null | head -1)
        if [ -n "$log_file" ]; then
            recent=$(tail -n 3 "$log_file" 2>/dev/null | grep -E "(Processing|Generated|Transcrib|✓|✗)" | tail -1)
            if [ -n "$recent" ]; then
                timestamp=$(echo "$recent" | grep -oP '\d{2}:\d{2}:\d{2}' | head -1 || echo "")
                echo -e "  ${CYAN}${service^^}:${NC} $(echo $recent | cut -c1-65)..."
            fi
        fi
    done
    echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────┘${NC}\n"
    
    echo -e "${YELLOW}Press Ctrl+C to exit | Refreshing every 3 seconds...${NC}"
    
    sleep 3
done
