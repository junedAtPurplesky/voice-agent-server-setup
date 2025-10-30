#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$BASE_DIR/venv/bin/activate"
source "$BASE_DIR/config/system.env"
source "$BASE_DIR/config/llm.env"
exec python "$BASE_DIR/services/llm_service/app/llm_main.py"
