# Carwash Management Platform

A multi-tenant car-wash management platform built around a **FastAPI + PostgreSQL** backend and a modern **Astro + React** web frontend.

The system is designed for multiple car-wash businesses sharing one deployment while keeping operational data isolated by tenant. It covers sales, expenses, customers, vehicles, service/product catalogs, reporting, authentication, and role-based permissions.

> Public portfolio repository. Deployment credentials, production data, and environment-specific secrets are intentionally excluded.

## Why this project matters

This is not a CRUD demo. The backend models a real operational workflow with tenant isolation, authenticated APIs, permission checks, database migrations, transactional writes, reporting, and deployment infrastructure.

The main engineering goals are:

- keep business logic outside HTTP handlers;
- isolate tenant data consistently;
- make schema evolution explicit with Alembic;
- keep the frontend contract synchronized with the FastAPI OpenAPI schema;
- support reproducible local and production-like environments with Docker;
- protect secrets and runtime configuration through environment variables.

## Architecture

```text
Browser
  │
  ▼
Astro + React frontend
  │  /api
  ▼
Nginx
  │
  ▼
FastAPI
  │
  ├── routers / schemas / dependencies
  ├── services
  ├── repositories
  └── SQLAlchemy 2.0
          │
          ▼
      PostgreSQL 16
```

The backend follows a layered structure:

```text
backend/
├── api/            FastAPI application, routers, schemas and dependencies
├── services/       domain/application logic
├── repositories/   persistence operations
├── database/       SQLAlchemy models and session management
├── alembic/        database migrations
├── cli/            operational commands
└── utils/          shared helpers
```

## Core capabilities

### Multi-tenancy

Each tenant is represented by a `lavanderia` and identified by subdomain/host.

- authenticated tokens carry the tenant identifier;
- repositories and services filter by `lavanderia_id`;
- protected endpoints validate the tenant context;
- the HTTP `Host` header can participate in tenant resolution.

### Authentication and authorization

The API issues signed Bearer tokens containing:

- user ID;
- tenant ID;
- permissions;
- issued-at time;
- expiration time.

Protected endpoints use shared FastAPI dependencies such as `get_current_user`, `require_permission(...)`, and `require_any_permission(...)`.

### Business domains

The current backend includes:

- sales and sale items;
- expenses and expense categories;
- customers;
- vehicles and vehicle types;
- services and products;
- roles and permissions;
- reports and exports.

Sales and expenses use logical voiding instead of destructive deletion in operational flows.

### Database

- PostgreSQL 16
- SQLAlchemy 2.0
- Alembic migrations
- seeded demo/admin data
- request-scoped transaction handling in migrated write paths

## API

FastAPI exposes endpoints for:

- authentication;
- catalogs;
- clients;
- sales;
- expenses;
- vehicles;
- reports;
- health checks.

Run the backend locally with:

```bash
uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

FastAPI provides the generated OpenAPI contract used by the web frontend to generate TypeScript API types.

## Frontend

The current web client is built with:

- Astro 5
- React 19
- Tailwind CSS 4
- TanStack Query
- React Hook Form
- Zod
- Zustand
- Recharts
- Vitest
- Testing Library
- Biome

Frontend API types are generated from the backend OpenAPI schema with `openapi-typescript`.

## Tests

The repository has a dedicated **CI workflow** that verifies the backend and frontend independently of deployment.

Current checks include:

- backend pytest suite;
- frontend Vitest suite;
- TypeScript type-checking;
- production frontend build.

Coverage includes authentication, catalogs, clients, expenses, sales, reports, vehicles, security, permissions and UI-related flows.

Typical backend test command:

```bash
uv run pytest
```

Frontend:

```bash
cd frontend/web
bun test
bun run type-check
bun run lint
```

## Docker

The repository includes Docker configuration for local and production-style deployments.

```text
docker-compose.yml
docker-compose.prod.yml
backend.Dockerfile
frontend/web/Dockerfile
```

The default stack contains:

- PostgreSQL;
- FastAPI backend;
- Nginx-served frontend.

Database startup is guarded by a PostgreSQL health check, and the backend starts only after the database becomes healthy.

## Local setup

Requirements:

- Python 3.13+
- `uv`
- Bun
- Docker + Docker Compose

Create your local environment file from the example:

```bash
cp .env.example .env
```

At minimum, set a strong authentication secret:

```bash
AUTH_TOKEN_SECRET=<random-secret>
```

A secure value can be generated with:

```bash
openssl rand -hex 32
```

Then start the stack:

```bash
docker compose up --build
```

## Engineering notes

The repository contains technical documentation under `docs/` plus a detailed backend status document at [backend/ESTADO_BACKEND.md](backend/ESTADO_BACKEND.md).

Some notable design choices:

- tenant resolution is treated as part of authorization rather than only routing;
- service/repository layers keep business rules out of FastAPI routers;
- database migrations are first-class artifacts;
- API errors are centralized instead of exposing persistence details;
- generated OpenAPI types reduce backend/frontend contract drift;
- secrets are expected through environment variables and are not committed.

## CI vs deployment

Code quality and deployment are intentionally separate concerns.

The CI workflow validates backend and frontend changes on pull requests and pushes. The deployment workflow is responsible only for delivery to the VPS after code checks pass. A deployment failure therefore does not imply that the application test suite failed.

## Current limitations / next work

The project is actively evolving. Remaining work includes:

- broader pagination/filtering for large lists;
- additional administrative user/role APIs;
- more PostgreSQL-backed integration tests;
- finishing migration of all write flows to request-scoped sessions;
- deployment hardening and logging review.

## Tech stack

**Backend:** Python · FastAPI · SQLAlchemy · PostgreSQL · Alembic · Pydantic · pytest · pandas · openpyxl

**Frontend:** Astro · React · TypeScript · Tailwind CSS · TanStack Query · Zod · Zustand · Vitest

**Infrastructure:** Docker · Docker Compose · Nginx

## Status

Active public portfolio project. The repository contains the application code, tests, migrations, Docker configuration and deployment workflow, while production secrets and operational data remain outside version control.
