#!/usr/bin/env bash
# Script que corre DENTRO del VPS via SSH (lo invoca el workflow de GitHub Actions).
#
# Hace:
#   1. cd al proyecto
#   2. git pull
#   3. docker compose up -d --build (con override de prod)
#   4. Smoke test: /api/health del frontend (proxy)
#
# El stdout/stderr de este script lo captura el job de Actions, asi que
# todo lo que imprime es visible en la UI de GitHub. Si algo falla,
# `set -e` aborta y el job queda en rojo.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/carwash-v2}"
COMPOSE_ARGS="-f docker-compose.yml -f docker-compose.prod.yml"
HEALTH_URL="http://carwash-v2-frontend-1/api/health"

echo "→ cd ${PROJECT_DIR}"
cd "${PROJECT_DIR}"

echo "→ git fetch + pull"
git fetch --all --prune
# Mantenemos la rama main, descartando cualquier cambio local (no deberia
# haber: el VPS solo es destino de deploys).
git reset --hard origin/main

echo "→ commit deployed:"
git log --oneline -1

echo "→ docker compose up -d --build (puede tardar)"
docker compose ${COMPOSE_ARGS} up -d --build

echo "→ Esperando que /api/health responda..."
for i in {1..30}; do
  # Hacemos el health check desde dentro de la red docker, usando el container
  # del frontend (es el mismo destino que pega NPM). Si responde, el stack
  # completo (front + back + db) esta vivo.
  if docker run --rm --network proxy curlimages/curl:latest \
       -sf "${HEALTH_URL}" >/dev/null 2>&1; then
    echo "✓ Stack healthy."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "✗ /api/health no respondio en 30 intentos. Logs recientes:" >&2
    docker compose ${COMPOSE_ARGS} logs --tail 30 backend frontend >&2
    exit 1
  fi
  sleep 2
done

echo "✓ Deploy completado: $(date -Is)"
