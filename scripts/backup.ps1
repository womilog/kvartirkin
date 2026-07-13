# ---------------------------------------------------------------------------
# Postgres backup for the kvartirkin project (Windows / PowerShell).
# Creates a plain .sql dump in .\backups with a timestamped name.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\backup.ps1
# ---------------------------------------------------------------------------
$ErrorActionPreference = 'Stop'

# Defaults; overridden by values read from .env below.
$dbUser = 'kvartirkin'
$dbName = 'kvartirkin_db'
if (Test-Path '.env') {
    Get-Content '.env' | ForEach-Object {
        if ($_ -match '^\s*DB_USER\s*=\s*(.+)$') { $dbUser = $Matches[1].Trim() }
        if ($_ -match '^\s*DB_NAME\s*=\s*(.+)$') { $dbName = $Matches[1].Trim() }
    }
}

New-Item -ItemType Directory -Force -Path 'backups' | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outFile = "backups\${dbName}_${timestamp}.sql"

Write-Host "Backing up database '$dbName' -> $outFile"

# pg_dump writes SQL to stdout; capture it as UTF-8 into the file.
$prevEnc = [Console]::OutputEncoding
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    docker compose exec -T db pg_dump -U $dbUser $dbName |
        Out-File -FilePath $outFile -Encoding utf8
}
finally {
    [Console]::OutputEncoding = $prevEnc
}

Write-Host "Done. Backup saved to $outFile"