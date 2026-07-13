#!/bin/sh
# ---------------------------------------------------------------------------
# Restore a Postgres backup for the kvartirkin project (Linux/macOS server).
#
# Usage:
#   ./scripts/restore.sh backups/kvartirkin_db_20240101_120000.sql.gz
#
# WARNING: this DROPS and recreates the existing data. Make a fresh backup
# first if you are unsure.
# ---------------------------------------------------------------------------
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [ -f .env ]; then
    # shellcheck disable=SC1091
    . ./.env
fi

DB_USER="${DB_USER:-kvartirkin}"
DB_NAME="${DB_NAME:-kvartirkin_db}"

printf "This will OVERWRITE all data in '%s'. Continue? [y/N] " "$DB_NAME"
read -r answer
case "$answer" in
    [yY]) ;;
    *) echo "Aborted."; exit 1 ;;
esac

echo "Restoring ${BACKUP_FILE} into '${DB_NAME}'..."
# Recreate a clean schema, then load the dump.
docker compose exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
gunzip -c "${BACKUP_FILE}" | docker compose exec -T db psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Restore complete."
