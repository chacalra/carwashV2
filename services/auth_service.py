"""Autenticacion y control de acceso."""

from repositories.role_permissions_repository import get_permissions_for_role
from repositories.users_repository import get_user_by_name, get_users_by_name
from utils.security import verify_password

# Permisos disponibles en el sistema. Clave = identificador interno, valor = etiqueta UI.
PERMISSIONS = {
    "dashboard": "Dashboard",
    "register_income": "Registrar ingresos",
    "register_expense": "Registrar egresos",
    "movements": "Movimientos",
    "export": "Exportar datos",
    "settings": "Configuracion",
    "edit_income": "Editar ingresos",
    "void_income": "Gestionar ingresos",
}

# Mapa de vista de navegacion → permiso requerido.
VIEW_PERMISSIONS = {
    "Dashboard": "dashboard",
    "Registrar ingreso": "register_income",
    "Editar ingreso": "edit_income",
    "Gestionar ingresos": "void_income",
    "Registrar egreso": "register_expense",
    "Movimientos": "movements",
    "Exportar": "export",
    "Configuracion": "settings",
}


def _resolve_login_user(name, lavanderia_id=None):
    """Resuelve el usuario de login respetando el modelo multi-tenant."""
    if lavanderia_id is not None:
        return get_user_by_name(name, lavanderia_id=lavanderia_id)

    users = get_users_by_name(name)
    if not users:
        return None
    if len(users) > 1:
        raise ValueError(
            "Ese usuario existe en varias lavanderias. Hace falta indicar la lavanderia para iniciar sesion."
        )
    return users[0]


def login(name, password, lavanderia_id=None):
    """
    Autentica un usuario por nombre y contrasena.
    Devuelve (user_row, permissions_list) o lanza ValueError.
    """
    if not name or not name.strip():
        raise ValueError("El nombre de usuario es obligatorio.")
    if not password:
        raise ValueError("La contrasena es obligatoria.")

    user = _resolve_login_user(name.strip(), lavanderia_id=lavanderia_id)

    if user is None or not user["is_active"]:
        raise ValueError("Usuario o contrasena incorrectos.")

    if not user["password_hash"]:
        raise ValueError("Usuario sin contrasena configurada. Contacte al administrador.")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("Usuario o contrasena incorrectos.")

    permissions = get_permissions_for_role(user["role_id"])
    return user, permissions


def get_allowed_views(permissions):
    """Devuelve la lista de vistas de navegacion a las que el usuario tiene acceso."""
    return [view for view, perm in VIEW_PERMISSIONS.items() if perm in permissions]
