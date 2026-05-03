"""Acceso a datos de usuarios del sistema."""

from datetime import datetime

from database.connection import get_connection


def get_all_users():
    """Devuelve todos los usuarios ordenados por nombre."""
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT id, name, role, is_active, created_at FROM users ORDER BY name ASC;"
        ).fetchall()
    finally:
        connection.close()


def get_user_by_name(name):
    """Busca un usuario por nombre (para login). Incluye password_hash."""
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT id, name, role, password_hash, is_active, created_at FROM users WHERE name = ?;",
            (name,),
        ).fetchone()
    finally:
        connection.close()


def create_user(name, role, password_hash):
    """Inserta un nuevo usuario con contrasena hasheada y devuelve su id."""
    connection = get_connection()
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            "INSERT INTO users (name, role, password_hash, is_active, created_at) VALUES (?, ?, ?, 1, ?);",
            (name, role, password_hash, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_user(user_id, name, role):
    """Actualiza nombre y rol de un usuario."""
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE users SET name = ?, role = ? WHERE id = ?;",
            (name, role, user_id),
        )
        connection.commit()
    finally:
        connection.close()


def update_user_password(user_id, password_hash):
    """Actualiza la contrasena de un usuario."""
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?;",
            (password_hash, user_id),
        )
        connection.commit()
    finally:
        connection.close()


def toggle_user(user_id):
    """Activa o desactiva un usuario."""
    connection = get_connection()
    try:
        connection.execute(
            "UPDATE users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?;",
            (user_id,),
        )
        connection.commit()
    finally:
        connection.close()
