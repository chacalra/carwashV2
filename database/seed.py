"""Carga inicial de catalogos por defecto."""

from datetime import datetime

from database.connection import get_connection
from utils.security import hash_password


# Roles y sus permisos por defecto.
# Las claves deben coincidir con PERMISSIONS en services/auth_service.py.
DEFAULT_ROLE_PERMISSIONS = {
    "maximo": [
        "dashboard",
        "register_income",
        "edit_income",
        "void_income",
        "register_expense",
        "movements",
        "export",
        "settings",
    ],
    "operador": [
        "register_income",
        "edit_income",
    ],
}


def seed_roles(connection):
    """Inserta los roles por defecto y sus permisos si no existen."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        connection.execute(
            "INSERT OR IGNORE INTO roles (name, is_active, created_at) VALUES (?, 1, ?);",
            (role_name, created_at),
        )
        for perm in permissions:
            connection.execute(
                "INSERT OR IGNORE INTO role_permissions (role_name, permission) VALUES (?, ?);",
                (role_name, perm),
            )


def seed_users(connection):
    """
    Crea el usuario Administrador si no existe.
    Si ya existe pero no tiene contrasena, le asigna 'admin' como contrasena inicial.
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing = connection.execute(
        "SELECT id, password_hash FROM users WHERE name = 'rafael';"
    ).fetchone()

    if existing is None:
        connection.execute(
            "INSERT INTO users (name, role, password_hash, is_active, created_at) VALUES (?, ?, ?, 1, ?);",
            ("rafael", "maximo", hash_password("admin"), created_at),
        )
    elif existing["password_hash"] is None:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?;",
            (hash_password("admin"), existing["id"]),
        )


DEFAULT_PRODUCTS = [
    "Hojas comunes",
    "GEL comun",
    "PERFUME comun",
    "AREON Hojas Dry",
    "AREON Paraguay",
    "AREON Brasil",
    "AREON Perfume Colgante",
    "AREON Fresh Wave / Zapatito",
    "AREON Smile / Peluche",
    "AREON Gel",
    "AREON GEL premium",
    "AREON Perfume Premium",
]


def seed_products(connection):
    """Inserta los productos por defecto si no existen."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for name in DEFAULT_PRODUCTS:
        connection.execute(
            "INSERT OR IGNORE INTO products (name, is_active, created_at) VALUES (?, 1, ?);",
            (name, created_at),
        )


def seed_initial_data():
    """Ejecuta toda la carga inicial de catalogos."""
    connection = get_connection()
    try:
        seed_roles(connection)
        seed_users(connection)
        seed_products(connection)
        connection.commit()
    finally:
        connection.close()
