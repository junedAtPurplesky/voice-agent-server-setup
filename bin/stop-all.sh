#!/bin/bash
################################################################################
# Stop All Voice Agent Services
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Stopping All Voice Agent Services...${NC}\n"

# Stop in reverse order (LLM -> TTS -> STT)
"$BASE_DIR/bin/stop-llm.sh"
"$BASE_DIR/bin/stop-tts.sh"
"$BASE_DIR/bin/stop-stt.sh"

echo -e "${BLUE}All services stopped.${NC}"
