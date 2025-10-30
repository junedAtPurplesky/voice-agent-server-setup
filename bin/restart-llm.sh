#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Restarting LLM Service..."
"$BASE_DIR/bin/stop-llm.sh"
sleep 2
"$BASE_DIR/bin/start-llm.sh"
