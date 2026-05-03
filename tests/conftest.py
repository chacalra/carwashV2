"""Fixtures compartidos para la suite de tests."""

import pytest
import database.connection as db_conn
from database.schema import create_tables


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Crea una base de datos SQLite temporal con todas las tablas.
    Parchea DB_PATH para que todos los repositorios usen esta base de datos.
    """
    db_path = tmp_path / "test_carwash.db"
    monkeypatch.setattr(db_conn, "DB_PATH", db_path)
    create_tables()
    return db_path
