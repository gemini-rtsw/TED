#!/usr/bin/env bash
# Usage: ./grafanaBackup.sh [backup_dir]

set -euo pipefail

CONTAINER="grafana"
DB_PATH="/var/lib/grafana/grafana.db"
BACKUP_DIR="${1:-$HOME/grafanaBackups}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/grafana.sql-$TIMESTAMP"

docker exec -i "$CONTAINER" sqlite3 "$DB_PATH" .dump > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"
