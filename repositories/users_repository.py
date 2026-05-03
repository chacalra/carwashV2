"""Acceso a datos de usuarios del sistema para la V2."""

from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import Lavanderia, Rol, Usuario
from utils.tenant_context import resolve_lavanderia_id


def _serialize_user(user, role=None, lavanderia=None):
    """Convierte una entidad Usuario en un diccionario amigable para UI y servicios."""
    role_name = role.nombre if role is not None else None
    lavanderia_name = lavanderia.nombre_local if lavanderia is not None else None

    return {
        "id": user.id,
        "name": user.nombre_usuario,
        "nombre_usuario": user.nombre_usuario,
        "role": role_name,
        "role_id": user.rol_id,
        "is_active": 1 if user.estado else 0,
        "estado": user.estado,
        "password_hash": user.password_hash,
        "created_at": user.created_at,
        "lavanderia_id": user.lavanderia_id,
        "lavanderia_name": lavanderia_name,
    }


def _resolve_role(session, role_id=None, role_name=None, lavanderia_id=None):
    """Busca un rol por id o por nombre y devuelve la entidad."""
    if role_id is not None:
        role = session.get(Rol, role_id)
        if role is None:
            raise ValueError("El rol indicado no existe.")
        if lavanderia_id is not None and role.lavanderia_id != lavanderia_id:
            raise ValueError("El rol indicado no pertenece a esa lavanderia.")
        return role

    if role_name is None or not str(role_name).strip():
        raise ValueError("El rol es obligatorio.")

    query = select(Rol).where(Rol.nombre == str(role_name).strip())
    if lavanderia_id is not None:
        query = query.where(Rol.lavanderia_id == lavanderia_id)

    roles = session.scalars(query).all()
    if not roles:
        raise ValueError("El rol indicado no existe.")
    if len(roles) > 1:
        raise ValueError(
            "El rol indicado existe en varias lavanderias. Hace falta especificar la lavanderia."
        )

    return roles[0]


def get_all_users(lavanderia_id=None):
    """Devuelve usuarios ordenados por nombre, opcionalmente filtrados por lavanderia."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        query = (
            select(Usuario, Rol, Lavanderia)
            .join(Rol, Usuario.rol_id == Rol.id)
            .join(Lavanderia, Usuario.lavanderia_id == Lavanderia.id)
            .order_by(Usuario.nombre_usuario.asc())
        )

        if resolved_lavanderia_id is not None:
            query = query.where(Usuario.lavanderia_id == resolved_lavanderia_id)

        rows = session.execute(query).all()
        return [_serialize_user(user, role, lavanderia) for user, role, lavanderia in rows]


def get_users_by_name(name):
    """Busca todos los usuarios que comparten un nombre de usuario."""
    clean_name = str(name).strip()
    if not clean_name:
        return []

    with SessionLocal() as session:
        query = (
            select(Usuario, Rol, Lavanderia)
            .join(Rol, Usuario.rol_id == Rol.id)
            .join(Lavanderia, Usuario.lavanderia_id == Lavanderia.id)
            .where(Usuario.nombre_usuario == clean_name)
            .order_by(Usuario.id.asc())
        )
        rows = session.execute(query).all()
        return [_serialize_user(user, role, lavanderia) for user, role, lavanderia in rows]


def get_user_by_name(name, lavanderia_id=None):
    """Busca un usuario por nombre, opcionalmente dentro de una lavanderia."""
    clean_name = str(name).strip()
    if not clean_name:
        return None
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        query = (
            select(Usuario, Rol, Lavanderia)
            .join(Rol, Usuario.rol_id == Rol.id)
            .join(Lavanderia, Usuario.lavanderia_id == Lavanderia.id)
            .where(Usuario.nombre_usuario == clean_name)
        )

        if resolved_lavanderia_id is not None:
            query = query.where(Usuario.lavanderia_id == resolved_lavanderia_id)

        row = session.execute(query.order_by(Usuario.id.asc())).first()
        if row is None:
            return None

        user, role, lavanderia = row
        return _serialize_user(user, role, lavanderia)


def get_user_by_id(user_id, lavanderia_id=None):
    """Busca un usuario por id, opcionalmente validando lavanderia."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        query = (
            select(Usuario, Rol, Lavanderia)
            .join(Rol, Usuario.rol_id == Rol.id)
            .join(Lavanderia, Usuario.lavanderia_id == Lavanderia.id)
            .where(Usuario.id == user_id)
        )

        if resolved_lavanderia_id is not None:
            query = query.where(Usuario.lavanderia_id == resolved_lavanderia_id)

        row = session.execute(query).first()
        if row is None:
            return None

        user, role, lavanderia = row
        return _serialize_user(user, role, lavanderia)


def create_user(name, role=None, password_hash=None, lavanderia_id=None, role_id=None):
    """Inserta un nuevo usuario con contrasena hasheada y devuelve su id."""
    clean_name = str(name).strip()
    if not clean_name:
        raise ValueError("El nombre del usuario es obligatorio.")
    if not password_hash:
        raise ValueError("La contrasena del usuario es obligatoria.")

    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        resolved_role = _resolve_role(
            session,
            role_id=role_id,
            role_name=role,
            lavanderia_id=resolved_lavanderia_id,
        )
        target_lavanderia_id = resolved_lavanderia_id or resolved_role.lavanderia_id

        user = Usuario(
            nombre_usuario=clean_name,
            password_hash=password_hash,
            estado=True,
            lavanderia_id=target_lavanderia_id,
            rol_id=resolved_role.id,
        )
        session.add(user)
        session.commit()
        return user.id


def update_user(user_id, name, role=None, lavanderia_id=None, role_id=None):
    """Actualiza nombre y rol de un usuario."""
    clean_name = str(name).strip()
    if not clean_name:
        raise ValueError("El nombre del usuario es obligatorio.")

    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        user = session.get(Usuario, user_id)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        if resolved_lavanderia_id is not None and user.lavanderia_id != resolved_lavanderia_id:
            raise ValueError("El usuario no pertenece a esa lavanderia.")

        resolved_role = _resolve_role(
            session,
            role_id=role_id,
            role_name=role,
            lavanderia_id=user.lavanderia_id,
        )

        user.nombre_usuario = clean_name
        user.rol_id = resolved_role.id
        session.commit()


def update_user_password(user_id, password_hash, lavanderia_id=None):
    """Actualiza la contrasena de un usuario."""
    if not password_hash:
        raise ValueError("La contrasena hasheada es obligatoria.")

    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        user = session.get(Usuario, user_id)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        if resolved_lavanderia_id is not None and user.lavanderia_id != resolved_lavanderia_id:
            raise ValueError("El usuario no pertenece a esa lavanderia.")

        user.password_hash = password_hash
        session.commit()


def toggle_user(user_id, lavanderia_id=None):
    """Activa o desactiva un usuario."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id)

    with SessionLocal() as session:
        user = session.get(Usuario, user_id)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        if resolved_lavanderia_id is not None and user.lavanderia_id != resolved_lavanderia_id:
            raise ValueError("El usuario no pertenece a esa lavanderia.")

        user.estado = not user.estado
        session.commit()
