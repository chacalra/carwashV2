"""Autenticacion y control de acceso."""

from repositories.role_permissions_repository import get_permissions_for_role
from repositories.users_repository import get_user_by_name
from services.tenant_service import get_tenant_by_host, get_tenant_by_id, get_tenant_by_subdominio
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
    "Registrar venta": "register_income",
    "Editar ingreso": "edit_income",
    "Gestionar ingresos": "void_income",
    "Registrar egreso": "register_expense",
    "Movimientos": "movements",
    "Exportar": "export",
    "Configuracion": "settings",
}


def _resolve_login_tenant(*, lavanderia_id=None, subdominio=None, host=None):
    """Resuelve la lavanderia de autenticacion antes de buscar el usuario."""
    if host is not None:
        lavanderia = get_tenant_by_host(host)
    elif subdominio is not None:
        lavanderia = get_tenant_by_subdominio(subdominio)
    elif lavanderia_id is not None:
        lavanderia = get_tenant_by_id(lavanderia_id)
    else:
        raise ValueError(
            "Hace falta indicar el host o subdominio de la lavanderia para iniciar sesion."
        )

    if not lavanderia.estado:
        raise ValueError("La lavanderia indicada no esta activa.")

    return lavanderia


def _resolve_login_user(name, *, lavanderia_id=None, subdominio=None, host=None):
    """Resuelve el usuario de login dentro de una lavanderia ya identificada."""
    lavanderia = _resolve_login_tenant(
        lavanderia_id=lavanderia_id,
        subdominio=subdominio,
        host=host,
    )
    return get_user_by_name(name, lavanderia_id=lavanderia.id)


def login(name, password, lavanderia_id=None, subdominio=None, host=None):
    """
    Autentica un usuario por nombre y contrasena.
    Devuelve (user_row, permissions_list) o lanza ValueError.
    """
    if not name or not name.strip():
        raise ValueError("El nombre de usuario es obligatorio.")
    if not password:
        raise ValueError("La contrasena es obligatoria.")

    user = _resolve_login_user(
        name.strip(),
        lavanderia_id=lavanderia_id,
        subdominio=subdominio,
        host=host,
    )

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
