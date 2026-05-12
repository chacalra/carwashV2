"""Alta atómica de un tenant nuevo.

Crea en una sola transacción:
  - lavanderia (con subdominio normalizado)
  - rol "admin" para esa lavanderia
  - asignación al rol de TODOS los permisos activos del catálogo global
  - usuario admin con la contraseña hasheada

Si cualquier paso falla, rollback completo. No deja tenants a medias.

La lógica vive en `_create_tenant_in_session(session, ...)` para ser
testeable con una sesión mockeable. `create_tenant(...)` es el envoltorio
público que abre `SessionLocal()`, hace commit en éxito y rollback en error.
"""

import re

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import Permiso, Rol, RolPermiso, Usuario
from backend.repositories.lavanderias_repository import (
    create_lavanderia,
    get_lavanderia_by_subdominio,
)
from backend.utils.security import hash_password


SUBDOMAIN_RE = re.compile(r"^[a-z0-9-]+$")
ADMIN_ROLE_NAME = "admin"
MIN_PASSWORD_LENGTH = 8


def normalize_subdomain(value):
    """Normaliza y valida un subdominio.

    Lowercase + trim. Acepta solo `[a-z0-9-]+`. Lanza ValueError si no parsea.
    """
    if value is None:
        raise ValueError("El subdominio es obligatorio.")
    raw = str(value).strip().lower()
    if not raw:
        raise ValueError("El subdominio es obligatorio.")
    if not SUBDOMAIN_RE.match(raw):
        raise ValueError(
            f"Subdominio inválido: {value!r}. Solo letras minúsculas, números y guiones."
        )
    return raw


def _require_text(value, field):
    """Valida que `value` sea una cadena no vacía y la devuelve trimeada."""
    if value is None:
        raise ValueError(f"{field} es obligatorio.")
    raw = str(value).strip()
    if not raw:
        raise ValueError(f"{field} es obligatorio.")
    return raw


def _validate_password(password):
    """Valida largo mínimo de la contraseña."""
    if password is None or password == "":
        raise ValueError("La contraseña del admin es obligatoria.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )
    return password


def _create_tenant_in_session(
    session,
    *,
    subdomain,
    name,
    responsible,
    admin_username,
    admin_password,
    email=None,
    phone=None,
):
    """Hace el alta en una sesión existente. Usa flush, no commit."""
    clean_subdomain = normalize_subdomain(subdomain)
    clean_name = _require_text(name, "El nombre de la lavandería")
    clean_responsible = _require_text(responsible, "El responsable")
    clean_admin_username = _require_text(admin_username, "El usuario admin")
    _validate_password(admin_password)

    if get_lavanderia_by_subdominio(session, clean_subdomain) is not None:
        raise ValueError(
            f"Ya existe un tenant con subdominio {clean_subdomain!r}."
        )

    lavanderia = create_lavanderia(
        session,
        nombre_local=clean_name,
        subdominio=clean_subdomain,
        nombre_responsable=clean_responsible,
        email=(email or None),
        telefono=(phone or None),
    )

    role = Rol(
        nombre=ADMIN_ROLE_NAME,
        estado=True,
        lavanderia_id=lavanderia.id,
    )
    session.add(role)
    session.flush()

    permisos = session.scalars(
        select(Permiso).where(Permiso.estado.is_(True))
    ).all()
    if not permisos:
        raise ValueError(
            "No hay permisos activos en el catálogo global. Corré el seed antes de crear tenants."
        )
    for permiso in permisos:
        session.add(RolPermiso(rol_id=role.id, permiso_id=permiso.id))
    session.flush()

    usuario = Usuario(
        nombre_usuario=clean_admin_username,
        password_hash=hash_password(admin_password),
        estado=True,
        lavanderia_id=lavanderia.id,
        rol_id=role.id,
    )
    session.add(usuario)
    session.flush()

    return {
        "lavanderia_id": lavanderia.id,
        "subdominio": lavanderia.subdominio,
        "nombre_local": lavanderia.nombre_local,
        "nombre_responsable": lavanderia.nombre_responsable,
        "email": lavanderia.email,
        "telefono": lavanderia.telefono,
        "role_id": role.id,
        "role_name": role.nombre,
        "permissions_count": len(permisos),
        "admin_user_id": usuario.id,
        "admin_username": usuario.nombre_usuario,
    }


def create_tenant(
    *,
    subdomain,
    name,
    responsible,
    admin_username,
    admin_password,
    email=None,
    phone=None,
):
    """Wrapper público: abre sesión, commitea o rollbackea según resultado."""
    session = SessionLocal()
    try:
        result = _create_tenant_in_session(
            session,
            subdomain=subdomain,
            name=name,
            responsible=responsible,
            admin_username=admin_username,
            admin_password=admin_password,
            email=email,
            phone=phone,
        )
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
