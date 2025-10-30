#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Restarting TTS Service..."
"$BASE_DIR/bin/stop-tts.sh"
sleep 2
"$BASE_DIR/bin/start-tts.sh"
