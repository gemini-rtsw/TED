#!/usr/bin/env bash
# Usage: ./grafanaBackup.sh [backup_dir]

set -euo pipefail

CONTAINER="grafana"
SRC_PATH="/var/lib/grafana/grafana.db"
BACKUP_DIR="${1:-$HOME/grafanaBackups}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/grafana.db-$TIMESTAMP.bak"

docker cp "$CONTAINER:$SRC_PATH" "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"
