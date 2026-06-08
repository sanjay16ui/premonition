# PREMONITION Backup Script (Windows PowerShell)
# Usage: .\scripts\backup.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$BackupDir = "backups\backup_$Stamp"
$Archive = "backups\premonition_backup_$Stamp.zip"

Write-Host "=== PREMONITION Backup (Windows) ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$DirsToBackup = @("models\artifacts", "reports", "logs", "data\processed")
foreach ($dir in $DirsToBackup) {
    if (Test-Path $dir) {
        Write-Host "Backing up $dir ..."
        Copy-Item -Recurse $dir "$BackupDir\"
    }
}

# Config
New-Item -ItemType Directory -Force -Path "$BackupDir\config" | Out-Null
Copy-Item "src\premonition\config\*.yaml" "$BackupDir\config\" -ErrorAction SilentlyContinue
Copy-Item ".env.example" "$BackupDir\config\" -ErrorAction SilentlyContinue

# Manifest
@{
    backup_timestamp = (Get-Date).ToUniversalTime().ToString("o")
    project = "PREMONITION"
    version = "0.1.0"
    contents = @("models", "reports", "logs", "data/processed", "config")
} | ConvertTo-Json | Set-Content "$BackupDir\manifest.json"

# Compress
Compress-Archive -Path $BackupDir -DestinationPath $Archive -Force
Remove-Item -Recurse -Force $BackupDir

Write-Host "Backup saved: $Archive" -ForegroundColor Green

# Retention: keep last 10
$backups = Get-ChildItem "backups\premonition_backup_*.zip" | Sort-Object LastWriteTime -Descending
if ($backups.Count -gt 10) {
    $backups | Select-Object -Skip 10 | Remove-Item -Force
    Write-Host "Retention: removed old backups (keeping last 10)"
}
