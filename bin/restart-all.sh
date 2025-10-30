#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$BASE_DIR/bin/stop-all.sh"
echo ""
sleep 3
"$BASE_DIR/bin/start-all.sh"
