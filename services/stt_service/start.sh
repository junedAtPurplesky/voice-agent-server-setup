#!/bin/bash
# Individual STT service starter (called by bin/start-stt.sh)

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/venv/bin/activate"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/stt.env"

exec python "$BASE_DIR/services/stt_service/app/stt_main.py"
