#!/bin/bash
# Clean up old log files (keeps last 7 days)

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$BASE_DIR/logs"

echo "Cleaning up logs older than 7 days..."

# Find and delete old logs
find "$LOG_DIR" -name "*.log" -mtime +7 -delete

echo "✓ Log cleanup complete"
du -sh "$LOG_DIR"/*
