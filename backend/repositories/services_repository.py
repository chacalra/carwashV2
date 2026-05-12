"""Acceso a datos del catalogo de servicios para la V2."""

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import DetalleVenta, Servicio
from backend.utils.tenant_context import resolve_lavanderia_id


def _serialize_service(service):
    """Convierte una entidad Servicio a un diccionario compatible con la UI actual."""
    return {
        "id": service.id,
        "name": service.nombre_servicio,
        "nombre_servicio": service.nombre_servicio,
        "price": service.precio,
        "precio": service.precio,
        "is_active": 1 if service.estado else 0,
        "estado": service.estado,
        "created_at": service.created_at,
        "lavanderia_id": service.lavanderia_id,
    }


def get_all_services(lavanderia_id=None):
    """Devuelve todos los servicios del tenant actual ordenados por nombre."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(Servicio)
            .where(Servicio.lavanderia_id == resolved_lavanderia_id)
            .order_by(Servicio.nombre_servicio.asc())
        )
        return [_serialize_service(service) for service in session.scalars(query).all()]


def get_active_services(lavanderia_id=None):
    """Devuelve solo los servicios activos del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(Servicio)
            .where(
                Servicio.lavanderia_id == resolved_lavanderia_id,
                Servicio.estado.is_(True),
            )
            .order_by(Servicio.nombre_servicio.asc())
        )
        return [_serialize_service(service) for service in session.scalars(query).all()]


def get_service_by_id(service_id, lavanderia_id=None):
    """Busca un servicio por id dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Servicio).where(
            Servicio.id == service_id,
            Servicio.lavanderia_id == resolved_lavanderia_id,
        )
        service = session.scalar(query)
        return _serialize_service(service) if service is not None else None


def create_service(name, lavanderia_id, price=0):
    """Inserta un nuevo servicio y devuelve su id."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        service = Servicio(
            nombre_servicio=name,
            precio=price,
            estado=True,
            lavanderia_id=resolved_lavanderia_id,
        )
        session.add(service)
        session.commit()
        return service.id


def update_service(service_id, name=None, price=None, lavanderia_id=None):
    """Actualiza nombre y/o precio de un servicio."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Servicio).where(
            Servicio.id == service_id,
            Servicio.lavanderia_id == resolved_lavanderia_id,
        )
        service = session.scalar(query)
        if service is None:
            raise ValueError("El servicio indicado no existe.")

        if name is not None:
            service.nombre_servicio = name
        if price is not None:
            service.precio = price
        session.commit()


def update_service_name(service_id, name, lavanderia_id=None):
    """Actualiza solo el nombre de un servicio."""
    update_service(service_id, name=name, lavanderia_id=lavanderia_id)


def is_service_in_use(service_id, lavanderia_id=None):
    """Devuelve True si algun detalle de venta referencia este servicio."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(DetalleVenta.id)
            .join(Servicio, Servicio.id == DetalleVenta.servicio_id)
            .where(
                DetalleVenta.servicio_id == service_id,
                Servicio.lavanderia_id == resolved_lavanderia_id,
            )
            .limit(1)
        )
        return session.scalar(query) is not None


def delete_service(service_id, lavanderia_id=None):
    """Elimina un servicio permanentemente."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Servicio).where(
            Servicio.id == service_id,
            Servicio.lavanderia_id == resolved_lavanderia_id,
        )
        service = session.scalar(query)
        if service is None:
            raise ValueError("El servicio indicado no existe.")

        session.delete(service)
        session.commit()


def toggle_service(service_id, lavanderia_id=None):
    """Activa o desactiva un servicio."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Servicio).where(
            Servicio.id == service_id,
            Servicio.lavanderia_id == resolved_lavanderia_id,
        )
        service = session.scalar(query)
        if service is None:
            raise ValueError("El servicio indicado no existe.")

        service.estado = not service.estado
        session.commit()
