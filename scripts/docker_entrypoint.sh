#!/usr/bin/env bash
# Entrypoint del container backend.
# 1. Espera a Postgres (timeout 30s).
# 2. Corre migraciones alembic.
# 3. Ejecuta el CMD pasado (uvicorn por default).
#
# Errores son fatales: si la DB no responde o las migrations fallan, el
# container cae y docker lo reinicia (restart policy).

set -euo pipefail

DB_HOST="${PGHOST:-db}"
DB_PORT="${PGPORT:-5432}"

echo "→ Esperando Postgres en ${DB_HOST}:${DB_PORT}..."
for i in {1..30}; do
  if python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('${DB_HOST}', ${DB_PORT}))" 2>/dev/null; then
    echo "✓ Postgres disponible."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "✗ Postgres no respondio en 30s. Aborto." >&2
    exit 1
  fi
  sleep 1
done

echo "→ Corriendo migraciones alembic..."
uv run alembic upgrade head

# Sembrar el catalogo global de permisos (idempotente: solo agrega los que
# faltan). Sin esto, create-tenant falla con "No hay permisos activos".
echo "→ Sembrando permisos globales..."
uv run python -c "
from backend.database.connection import SessionLocal
from backend.database.seed import seed_permissions
with SessionLocal() as s:
    seed_permissions(s)
    s.commit()
print('  permisos OK')
"

echo "→ Arrancando: $*"
exec "$@"
