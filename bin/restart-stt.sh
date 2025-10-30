#!/bin/bash
################################################################################
# Restart STT Service
################################################################################

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Restarting STT Service..."
"$BASE_DIR/bin/stop-stt.sh"
sleep 2
"$BASE_DIR/bin/start-stt.sh"
