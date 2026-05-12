"""FastAPI entrypoint for the AutoCare backend."""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from backend.api.routers import (
    auth,
    catalogs,
    clients,
    expenses,
    health,
    permissions,
    reports,
    roles,
    sales,
    users,
    vehicles,
)

logger = logging.getLogger(__name__)

_DEV_SECRET = "dev-secret-change-me"


def create_app() -> FastAPI:
    """Builds the FastAPI application."""
    if os.environ.get("AUTH_TOKEN_SECRET", _DEV_SECRET) == _DEV_SECRET:
        logger.warning(
            "AUTH_TOKEN_SECRET no esta configurado. "
            "Usando clave de desarrollo. NO usar en produccion."
        )

    app = FastAPI(
        title="AutoCare Backend",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=os.environ.get(
            "CORS_ALLOW_ORIGIN_REGEX",
            r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.error("IntegrityError on %s: %s", request.url.path, exc.orig)
        return JSONResponse(
            status_code=409,
            content={"detail": "El registro ya existe o viola una restriccion de integridad."},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor."},
        )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(catalogs.router)
    app.include_router(clients.router)
    app.include_router(sales.router)
    app.include_router(expenses.router)
    app.include_router(vehicles.router)
    app.include_router(reports.router)
    app.include_router(permissions.router)
    app.include_router(roles.router)
    app.include_router(users.router)
    return app


app = create_app()
