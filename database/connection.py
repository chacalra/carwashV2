"""Conexion centralizada a SQLite."""

import os
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
_data_dir = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
DB_PATH = _data_dir / "carwash.db"


def enable_foreign_keys(connection):
    """Activa el soporte de foreign keys para la conexion actual."""
    connection.execute("PRAGMA foreign_keys = ON;")


def get_connection():
    """Crea y devuelve una conexion SQLite lista para usar."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    enable_foreign_keys(connection)
    return connection
