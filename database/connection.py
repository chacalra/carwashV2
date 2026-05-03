"""Conexion centralizada con SQLAlchemy 2.0 sobre PostgreSQL."""

import os
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()


def _build_database_url():
    """Construye DATABASE_URL si no fue definida explícitamente."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD", "")
    database = os.environ.get("PGDATABASE", "carwash")

    auth = quote(user)
    if password:
        auth = f"{auth}:{quote(password)}"

    return f"postgresql+psycopg://{auth}@{host}:{port}/{database}"


DATABASE_URL = _build_database_url()


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session():
    """Entrega una sesión SQLAlchemy y garantiza su cierre."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
