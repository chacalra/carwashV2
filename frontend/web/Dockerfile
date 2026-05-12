# Frontend Astro/React build estatico servido por nginx alpine.
#
# Multi-stage:
#   1. builder: bun install + bun run build  -> /app/dist
#   2. runtime: nginx:alpine sirviendo /app/dist en :80
#
# `PUBLIC_API_BASE_URL` se inyecta al build (Astro lo embebe en JS estatico).

FROM oven/bun:latest AS builder

WORKDIR /app

# Cache de deps separado del codigo.
COPY package.json bun.lock* bun.lockb* ./
RUN bun install --frozen-lockfile || bun install

COPY . .

# El default apunta al backend dentro del compose (servicio "backend").
# En prod se sobreescribe con `https://<dominio>/api` via build-arg.
ARG PUBLIC_API_BASE_URL=/api
ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}

RUN bun run build

# --- runtime ---
FROM nginx:1.27-alpine

# Config nginx con fallback a index.html (SPA estilo Astro static).
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck simple: la home debe responder 200.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1
