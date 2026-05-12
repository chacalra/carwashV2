# Backend FastAPI dockerizado con uv.
#
# Stage unico (la imagen final ya es chica con python:slim + uv).
# Si en algun momento queremos achicar mas, separamos build/run y copiamos
# solo el venv resuelto.

FROM python:3.13-slim AS base

# Instalamos uv. Pinneado al binario oficial: rapido y reproducible.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Buenas practicas: no .pyc, salida sin buffer, mejor para logs en docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Resolvemos deps con cache de Docker: si solo cambia codigo, esto no se rehace.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Codigo del backend (incluye backend/alembic), alembic.ini en raiz, scripts.
COPY backend ./backend
COPY alembic.ini ./
COPY scripts ./scripts

# Instalamos el proyecto en si (para los entrypoints como `python -m backend.cli`).
RUN uv sync --frozen --no-dev

EXPOSE 8000

# El backend espera la DB antes de arrancar (uvicorn fallaria sino).
# El entrypoint corre migrations y despues uvicorn.
COPY scripts/docker_entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
