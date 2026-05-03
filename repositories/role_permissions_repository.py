"""Acceso a datos de permisos por rol."""

from database.connection import get_connection


def get_permissions_for_role(role_name):
    """Devuelve la lista de permisos asignados a un rol."""
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT permission FROM role_permissions WHERE role_name = ?;",
            (role_name,),
        ).fetchall()
        return [row["permission"] for row in rows]
    finally:
        connection.close()


def set_permissions_for_role(role_name, permissions):
    """Reemplaza todos los permisos de un rol con la lista proporcionada."""
    connection = get_connection()
    try:
        connection.execute(
            "DELETE FROM role_permissions WHERE role_name = ?;",
            (role_name,),
        )
        for perm in permissions:
            connection.execute(
                "INSERT OR IGNORE INTO role_permissions (role_name, permission) VALUES (?, ?);",
                (role_name, perm),
            )
        connection.commit()
    finally:
        connection.close()
