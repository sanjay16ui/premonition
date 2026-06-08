#!/usr/bin/env bash
# PREMONITION Backup Script (Linux/macOS)
# Usage: bash scripts/backup.sh
# Creates timestamped archive of models, logs, reports, and configs.

set -euo pipefail
cd "$(dirname "$0")/.."

STAMP=$(date -u +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups/backup_${STAMP}"
ARCHIVE="backups/premonition_backup_${STAMP}.tar.gz"

echo "=== PREMONITION Backup ==="
mkdir -p "$BACKUP_DIR"

# Copy critical artifacts
for dir in models/artifacts reports logs data/processed; do
    if [ -d "$dir" ]; then
        echo "Backing up $dir ..."
        cp -r "$dir" "$BACKUP_DIR/"
    fi
done

# Copy configuration
mkdir -p "$BACKUP_DIR/config"
cp -r src/premonition/config/*.yaml "$BACKUP_DIR/config/" 2>/dev/null || true
cp .env.example "$BACKUP_DIR/config/" 2>/dev/null || true

# Create manifest
cat > "$BACKUP_DIR/manifest.json" <<EOF
{
  "backup_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "project": "PREMONITION",
  "version": "0.1.0",
  "contents": ["models", "reports", "logs", "data/processed", "config"]
}
EOF

# Compress
tar -czf "$ARCHIVE" -C backups "backup_${STAMP}"
rm -rf "$BACKUP_DIR"

echo "Backup saved: $ARCHIVE"
echo "Size: $(du -h "$ARCHIVE" | cut -f1)"

# Retention: keep last 10 backups
ls -t backups/premonition_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
echo "Retention: keeping last 10 backups"
