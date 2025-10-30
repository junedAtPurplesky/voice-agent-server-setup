#!/bin/bash
# Backup configuration files

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="$BASE_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Backing up configuration files..."

tar -czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" \
    -C "$BASE_DIR" config/

echo "✓ Backup created: $BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"
ls -lh "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"
