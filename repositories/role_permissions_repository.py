"""Acceso a datos de permisos por rol para la V2."""

from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import Permiso, Rol, RolPermiso


def _resolve_role(session, role_ref, lavanderia_id=None):
    """Resuelve un rol a partir de id o nombre."""
    if isinstance(role_ref, int):
        query = select(Rol).where(Rol.id == role_ref)
        if lavanderia_id is not None:
            query = query.where(Rol.lavanderia_id == lavanderia_id)
        role = session.scalar(query)
        if role is None:
            raise ValueError("El rol indicado no existe.")
        return role

    clean_name = str(role_ref).strip()
    query = select(Rol).where(Rol.nombre == clean_name)
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


def get_permissions_for_role(role_ref, lavanderia_id=None):
    """Devuelve la lista de permisos asignados a un rol por codigo."""
    try:
        with SessionLocal() as session:
            role = _resolve_role(session, role_ref, lavanderia_id=lavanderia_id)
            query = (
                select(Permiso.codigo)
                .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
                .where(RolPermiso.rol_id == role.id)
                .order_by(Permiso.codigo.asc())
            )
            return list(session.scalars(query).all())
    except ValueError:
        return []


def set_permissions_for_role(role_ref, permissions, lavanderia_id=None):
    """Reemplaza todos los permisos de un rol con la lista proporcionada."""
    with SessionLocal() as session:
        role = _resolve_role(session, role_ref, lavanderia_id=lavanderia_id)

        valid_codes = {
            permiso.codigo: permiso
            for permiso in session.scalars(select(Permiso)).all()
        }

        requested_codes = []
        for permission_code in permissions:
            code = str(permission_code).strip()
            if not code:
                continue
            if code not in valid_codes:
                raise ValueError(f"El permiso '{code}' no existe.")
            requested_codes.append(code)

        current_links = session.scalars(
            select(RolPermiso).where(RolPermiso.rol_id == role.id)
        ).all()
        for link in current_links:
            session.delete(link)

        for code in requested_codes:
            session.add(
                RolPermiso(
                    rol_id=role.id,
                    permiso_id=valid_codes[code].id,
                )
            )

        session.commit()
