#!/bin/sh
# ---------------------------------------------------------------------------
# Postgres backup for the kvartirkin project (Linux/macOS server).
# Creates a compressed SQL dump in ./backups with a timestamped name.
#
# Usage:
#   ./scripts/backup.sh
# ---------------------------------------------------------------------------
set -e

# Load DB_USER / DB_NAME from .env so we don't hardcode credentials here.
if [ -f .env ]; then
    # shellcheck disable=SC1091
    . ./.env
fi

DB_USER="${DB_USER:-kvartirkin}"
DB_NAME="${DB_NAME:-kvartirkin_db}"

mkdir -p backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTFILE="backups/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Backing up database '${DB_NAME}' -> ${OUTFILE}"
docker compose exec -T db pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${OUTFILE}"

echo "Done. Backup saved to ${OUTFILE}"
