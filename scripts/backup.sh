#!/bin/bash
set -euo pipefail

# --- Configurable variables ---
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cortex}"
DB_USER="${DB_USER:-cortex}"
CORTEX_ROOT="${CORTEX_ROOT:-}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# --- Derived ---
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DATE"
ERRORS=()

mkdir -p "$BACKUP_PATH"

# --- Step 1: PostgreSQL dump ---
if [ -n "$DB_HOST" ]; then
    echo "[1/3] Dumping PostgreSQL database '$DB_NAME' on $DB_HOST:$DB_PORT..."
    DUMP_FILE="$BACKUP_PATH/db_$DATE.sql.gz"
    if PGPASSWORD="${DB_PASSWORD:-}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null | gzip > "$DUMP_FILE"; then
        echo "      Database dump saved: $DUMP_FILE ($(du -h "$DUMP_FILE" | cut -f1))"
    else
        echo "      WARNING: Database dump failed — skipping."
        rm -f "$DUMP_FILE"
        ERRORS+=("Database dump failed")
    fi
else
    echo "[1/3] DB_HOST is empty — skipping database backup."
fi

# --- Step 2: CortexMemory archive ---
echo "[2/3] Archiving CortexMemory..."
if [ -n "$CORTEX_ROOT" ] && [ -d "$CORTEX_ROOT" ]; then
    STORAGE_FILE="$BACKUP_PATH/storage_$DATE.tar.gz"
    if tar -czf "$STORAGE_FILE" -C "$(dirname "$CORTEX_ROOT")" "$(basename "$CORTEX_ROOT")" 2>/dev/null; then
        echo "      Archive saved: $STORAGE_FILE ($(du -h "$STORAGE_FILE" | cut -f1))"
    else
        echo "      WARNING: Archiving CortexMemory failed — skipping."
        rm -f "$STORAGE_FILE"
        ERRORS+=("CortexMemory archive failed")
    fi
else
    echo "      CORTEX_ROOT is not set or directory does not exist — skipping."
fi

# --- Step 3: Rotate old backups ---
echo "[3/3] Rotating backups older than $RETENTION_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" -print -exec rm -rf {} + 2>/dev/null | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "      Removed $DELETED old backup(s)."
else
    echo "      No old backups to remove."
fi

# --- Summary ---
echo ""
echo "========================================"
echo " Backup Summary"
echo "========================================"
echo "  Timestamp:  $DATE"
echo "  Directory:  $BACKUP_PATH"
echo "  Contents:"
ls -lh "$BACKUP_PATH" 2>/dev/null | tail -n +2 | sed 's/^/    /'
echo ""

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "  Warnings (${#ERRORS[@]}):"
    for err in "${ERRORS[@]}"; do
        echo "    - $err"
    done
    echo ""
    echo "  Backup completed with warnings."
    exit 1
else
    echo "  Backup completed successfully."
fi
