#!/usr/bin/env bash
# Backup content_factory Postgres before first prod boot or before schema deploy.
set -euo pipefail

DB_NAME="${CFBOT_DB_NAME:-content_factory}"
BACKUP_DIR="${CFBOT_BACKUP_DIR:-/root/backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/cfbot-${STAMP}.dump"

install -d -m 700 "$BACKUP_DIR"
sudo -u postgres pg_dump -Fc "$DB_NAME" >"$OUT"
echo "Wrote $OUT ($(du -h "$OUT" | cut -f1))"
