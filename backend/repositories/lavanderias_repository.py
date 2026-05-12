"""Acceso a datos de lavanderias para la V2."""

from sqlalchemy import select

from backend.database.schema import Lavanderia


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


# --- Branding (iter B1) ---

# Sentinel para distinguir "no se pasó el campo" de "explícitamente None".
_UNSET = object()


def update_lavanderia_branding(
    session,
    lavanderia,
    *,
    logo_url=_UNSET,
    logo_url_dark=_UNSET,
    color_primario=_UNSET,
    color_secundario=_UNSET,
    mostrar_marca_mukusoft=_UNSET,
):
    """Actualiza solo los campos de branding pasados.

    Cualquier campo no pasado mantiene su valor actual. Pasar `None` borra
    el valor (lo deja null en DB).
    """
    if logo_url is not _UNSET:
        lavanderia.logo_url = logo_url
    if logo_url_dark is not _UNSET:
        lavanderia.logo_url_dark = logo_url_dark
    if color_primario is not _UNSET:
        lavanderia.color_primario = color_primario
    if color_secundario is not _UNSET:
        lavanderia.color_secundario = color_secundario
    if mostrar_marca_mukusoft is not _UNSET:
        lavanderia.mostrar_marca_mukusoft = bool(mostrar_marca_mukusoft)
    session.flush()
    return lavanderia


def get_lavanderia_branding(lavanderia):
    """Devuelve un dict serializable del branding actual del tenant."""
    return {
        "logo_url": lavanderia.logo_url,
        "logo_url_dark": lavanderia.logo_url_dark,
        "color_primario": lavanderia.color_primario,
        "color_secundario": lavanderia.color_secundario,
        "mostrar_marca_mukusoft": lavanderia.mostrar_marca_mukusoft,
    }
