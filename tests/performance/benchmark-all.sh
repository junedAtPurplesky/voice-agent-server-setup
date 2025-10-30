#!/bin/bash
################################################################################
# Comprehensive Performance Benchmark
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/stt.env"
source "$BASE_DIR/config/tts.env"
source "$BASE_DIR/config/llm.env"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         Voice Agent Performance Benchmark Suite                 ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"

# Run individual benchmarks
"$BASE_DIR/tests/performance/benchmark-stt.sh"
echo ""
"$BASE_DIR/tests/performance/benchmark-tts.sh"
echo ""
"$BASE_DIR/tests/performance/benchmark-llm.sh"
echo ""

# GPU Summary
echo -e "${YELLOW}═══ GPU Resource Summary ═══${NC}"
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,power.draw --format=csv,noheader,nounits | \
while IFS=',' read -r mem_used mem_total gpu_util power; do
    mem_percent=$((mem_used * 100 / mem_total))
    echo -e "${BLUE}VRAM:${NC} ${mem_used}MB / ${mem_total}MB (${mem_percent}%)"
    echo -e "${BLUE}GPU Utilization:${NC} ${gpu_util}%"
    echo -e "${BLUE}Power:${NC} ${power}W"
    
    if [ $mem_used -lt 20000 ]; then
        echo -e "${GREEN}✓ Excellent VRAM efficiency (AWQ quantization working)${NC}"
    fi
done

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Performance Benchmark Complete!                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
