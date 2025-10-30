#!/bin/bash
################################################################################
# Start All Voice Agent Services
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                          ║${NC}"
echo -e "${CYAN}║      ${BOLD}Starting All Voice Agent Services${NC}${CYAN}                  ║${NC}"
echo -e "${CYAN}║                                                          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

# Start services in order (STT -> TTS -> LLM)
"$BASE_DIR/bin/start-stt.sh"
echo ""
"$BASE_DIR/bin/start-tts.sh"
echo ""
"$BASE_DIR/bin/start-llm.sh"
echo ""

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      ${BOLD}All Services Started Successfully!${NC}${CYAN}                 ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

# Show status
"$BASE_DIR/bin/status-all.sh"
