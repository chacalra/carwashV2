"""Acceso a datos de roles del sistema para la V2."""

from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import Rol


def _serialize_role(role):
    """Convierte una entidad Rol en un diccionario amigable para UI."""
    return {
        "id": role.id,
        "name": role.nombre,
        "nombre": role.nombre,
        "is_active": 1 if role.estado else 0,
        "estado": role.estado,
        "created_at": role.created_at,
        "lavanderia_id": role.lavanderia_id,
    }


def get_all_roles(lavanderia_id=None):
    """Devuelve roles ordenados por nombre, opcionalmente filtrados por lavanderia."""
    with SessionLocal() as session:
        query = select(Rol).order_by(Rol.nombre.asc())
        if lavanderia_id is not None:
            query = query.where(Rol.lavanderia_id == lavanderia_id)
        return [_serialize_role(role) for role in session.scalars(query).all()]


def get_active_roles(lavanderia_id=None):
    """Devuelve solo los roles activos."""
    with SessionLocal() as session:
        query = select(Rol).where(Rol.estado.is_(True)).order_by(Rol.nombre.asc())
        if lavanderia_id is not None:
            query = query.where(Rol.lavanderia_id == lavanderia_id)
        return [_serialize_role(role) for role in session.scalars(query).all()]


def get_role_by_id(role_id, lavanderia_id=None):
    """Busca un rol por id, opcionalmente validando lavanderia."""
    with SessionLocal() as session:
        query = select(Rol).where(Rol.id == role_id)
        if lavanderia_id is not None:
            query = query.where(Rol.lavanderia_id == lavanderia_id)
        role = session.scalar(query)
        return _serialize_role(role) if role is not None else None


def get_role_by_name(name, lavanderia_id=None):
    """Busca un rol por nombre, opcionalmente dentro de una lavanderia."""
    clean_name = str(name).strip()
    if not clean_name:
        return None

    with SessionLocal() as session:
        query = select(Rol).where(Rol.nombre == clean_name)
        if lavanderia_id is not None:
            query = query.where(Rol.lavanderia_id == lavanderia_id)
        role = session.scalar(query.order_by(Rol.id.asc()))
        return _serialize_role(role) if role is not None else None


def create_role(name, lavanderia_id):
    """Inserta un nuevo rol y devuelve su id."""
    clean_name = str(name).strip()
    if not clean_name:
        raise ValueError("El nombre del rol es obligatorio.")

    with SessionLocal() as session:
        role = Rol(
            nombre=clean_name,
            estado=True,
            lavanderia_id=lavanderia_id,
        )
        session.add(role)
        session.commit()
        return role.id


def toggle_role(role_id, lavanderia_id=None):
    """Activa o desactiva un rol."""
    with SessionLocal() as session:
        query = select(Rol).where(Rol.id == role_id)
        if lavanderia_id is not None:
            query = query.where(Rol.lavanderia_id == lavanderia_id)
        role = session.scalar(query)
        if role is None:
            raise ValueError("El rol indicado no existe.")

        role.estado = not role.estado
        session.commit()
