"""Acceso a datos de lavanderias para la V2."""

from sqlalchemy import select

from database.schema import Lavanderia


def list_lavanderias(session, only_active=False):
    """Devuelve lavanderias ordenadas por nombre."""
    query = select(Lavanderia).order_by(Lavanderia.nombre_local.asc())

    if only_active:
        query = query.where(Lavanderia.estado.is_(True))

    return session.scalars(query).all()


def get_lavanderia_by_id(session, lavanderia_id):
    """Busca una lavanderia por su id."""
    query = select(Lavanderia).where(Lavanderia.id == lavanderia_id)
    return session.scalar(query)


def get_lavanderia_by_nombre_local(session, nombre_local):
    """Busca una lavanderia por nombre local."""
    query = select(Lavanderia).where(Lavanderia.nombre_local == nombre_local)
    return session.scalar(query)


def get_lavanderia_by_subdominio(session, subdominio):
    """Busca una lavanderia por subdominio."""
    query = select(Lavanderia).where(Lavanderia.subdominio == subdominio)
    return session.scalar(query)


def create_lavanderia(
    session,
    *,
    nombre_local,
    subdominio,
    nombre_responsable,
    email=None,
    telefono=None,
    estado=True,
):
    """Crea una lavanderia y devuelve la entidad persistida."""
    lavanderia = Lavanderia(
        nombre_local=nombre_local,
        subdominio=subdominio,
        nombre_responsable=nombre_responsable,
        email=email,
        telefono=telefono,
        estado=estado,
    )
    session.add(lavanderia)
    session.flush()
    return lavanderia


def update_lavanderia(
    session,
    lavanderia,
    *,
    nombre_local,
    subdominio,
    nombre_responsable,
    email=None,
    telefono=None,
):
    """Actualiza los datos principales de una lavanderia."""
    lavanderia.nombre_local = nombre_local
    lavanderia.subdominio = subdominio
    lavanderia.nombre_responsable = nombre_responsable
    lavanderia.email = email
    lavanderia.telefono = telefono
    session.flush()
    return lavanderia


def set_lavanderia_status(session, lavanderia, estado):
    """Activa o desactiva una lavanderia."""
    lavanderia.estado = estado
    session.flush()
    return lavanderia
