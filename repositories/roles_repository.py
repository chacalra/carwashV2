"""Acceso a datos de roles del sistema."""

from datetime import datetime

from database.connection import get_connection


def get_all_roles():
    """Devuelve todos los roles ordenados por nombre."""
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT id, name, is_active, created_at FROM roles ORDER BY name ASC;"
        ).fetchall()
    finally:
        connection.close()


def get_active_roles():
    """Devuelve solo los roles activos ordenados por nombre."""
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT id, name, is_active, created_at FROM roles WHERE is_active = 1 ORDER BY name ASC;"
        ).fetchall()
    finally:
        connection.close()


def create_role(name):
    """Inserta un nuevo rol y devuelve su id."""
    connection = get_connection()
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            "INSERT INTO roles (name, is_active, created_at) VALUES (?, 1, ?);",
            (name, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def toggle_role(role_id):
    """Activa o desactiva un rol."""
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE roles SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?;",
            (role_id,),
        )
        connection.commit()
    finally:
        connection.close()
