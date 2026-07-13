# ---------------------------------------------------------------------------
# Restore a Postgres backup for the kvartirkin project (Windows / PowerShell).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\restore.ps1 backups\kvartirkin_db_20240101_120000.sql
#
# WARNING: this DROPS and recreates the existing schema. Make a fresh backup
# first if you are unsure.
# ---------------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

$dbUser = 'kvartirkin'
$dbName = 'kvartirkin_db'
if (Test-Path '.env') {
    Get-Content '.env' | ForEach-Object {
        if ($_ -match '^\s*DB_USER\s*=\s*(.+)$') { $dbUser = $Matches[1].Trim() }
        if ($_ -match '^\s*DB_NAME\s*=\s*(.+)$') { $dbName = $Matches[1].Trim() }
    }
}

$answer = Read-Host "This will OVERWRITE all data in '$dbName'. Continue? [y/N]"
if ($answer -notmatch '^[yY]$') {
    Write-Host 'Aborted.'
    exit 1
}

Write-Host "Restoring $BackupFile into '$dbName'..."

# Recreate a clean schema, then load the dump.
docker compose exec -T db psql -U $dbUser -d $dbName -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
Get-Content $BackupFile -Raw | docker compose exec -T db psql -U $dbUser -d $dbName

Write-Host 'Restore complete.'