#!/usr/bin/env bash
# Backup diario de la base Postgres del stack docker compose.
#
# Pensado para corrercon cron en el VPS de produccion. Genera un dump
# comprimido con timestamp en ~/backups/ y borra los mas viejos que
# `RETENTION_DAYS` para no llenar disco.
#
# Uso manual:
#   bash scripts/backup_db.sh
#
# Uso en cron (3 AM diario):
#   0 3 * * * /home/ramon/projects/carwash-v2/scripts/backup_db.sh \
#     >> /home/ramon/backups/backup.log 2>&1

set -euo pipefail

# --- config (ajustable por env vars) ---
PROJECT_DIR="${PROJECT_DIR:-/home/ramon/projects/carwash-v2}"
BACKUP_DIR="${BACKUP_DIR:-/home/ramon/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# --- run ---
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_FILE="${BACKUP_DIR}/carwash-${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

cd "${PROJECT_DIR}"

# pg_dump corre dentro del container db. -T (sin TTY) hace que funcione
# desde cron. Las credenciales las toma del entorno del container.
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
  pg_dump -U carwash -d carwash | gzip > "${OUT_FILE}"

# Validar que el archivo no este vacio.
if [ ! -s "${OUT_FILE}" ]; then
  echo "[$(date -Is)] ERROR: backup vacio en ${OUT_FILE}" >&2
  rm -f "${OUT_FILE}"
  exit 1
fi

SIZE=$(du -h "${OUT_FILE}" | cut -f1)
echo "[$(date -Is)] OK: ${OUT_FILE} (${SIZE})"

# Limpiar los mas viejos que RETENTION_DAYS.
find "${BACKUP_DIR}" -name "carwash-*.sql.gz" -type f -mtime "+${RETENTION_DAYS}" -delete \
  -printf "[%TY-%Tm-%Td] borrado por retencion: %p\n" 2>/dev/null || true
