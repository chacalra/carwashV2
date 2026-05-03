#!/bin/bash
# Descarga la base de datos de Render y reemplaza la local.
# Guarda un backup del dia anterior antes de reemplazar.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_DB="$PROJECT_DIR/data/carwash.db"
BACKUP_DB="$PROJECT_DIR/data/carwash.db.bak"
LOG_FILE="$PROJECT_DIR/data/sync.log"
RENDER_HOST="srv-d7gee2flk1mc7386jocg@ssh.ohio.render.com"
RENDER_DB="/var/data/carwash.db/carwash.db"
SSH_KEY="$HOME/.ssh/render_key"

timestamp() { date "+%Y-%m-%d %H:%M:%S"; }

echo "[$(timestamp)] Iniciando sync desde Render..." >> "$LOG_FILE"

# Backup del local actual
if [ -f "$LOCAL_DB" ]; then
    cp "$LOCAL_DB" "$BACKUP_DB"
    echo "[$(timestamp)] Backup guardado en $BACKUP_DB" >> "$LOG_FILE"
fi

# Descarga desde Render
scp -i "$SSH_KEY" \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=30 \
    "$RENDER_HOST:$RENDER_DB" "$LOCAL_DB"

echo "[$(timestamp)] Sync completado. DB local actualizada." >> "$LOG_FILE"
