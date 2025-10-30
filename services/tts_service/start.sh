#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/venv/bin/activate"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/tts.env"
exec python "$BASE_DIR/services/tts_service/app/tts_main.py"
