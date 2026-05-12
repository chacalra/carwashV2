"""Acceso a datos del catalogo de tipos de vehiculo para la V2."""

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import TipoVehiculo, Vehiculo
from backend.utils.tenant_context import resolve_lavanderia_id


def _serialize_vehicle_type(vehicle_type):
    """Convierte una entidad TipoVehiculo a un diccionario compatible con la UI actual."""
    return {
        "id": vehicle_type.id,
        "name": vehicle_type.nombre,
        "nombre": vehicle_type.nombre,
        "is_active": 1 if vehicle_type.estado else 0,
        "estado": vehicle_type.estado,
        "created_at": vehicle_type.created_at,
        "lavanderia_id": vehicle_type.lavanderia_id,
    }


def get_all_vehicle_types(lavanderia_id=None):
    """Devuelve todos los tipos de vehiculo del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(TipoVehiculo)
            .where(TipoVehiculo.lavanderia_id == resolved_lavanderia_id)
            .order_by(TipoVehiculo.nombre.asc())
        )
        return [
            _serialize_vehicle_type(vehicle_type)
            for vehicle_type in session.scalars(query).all()
        ]


def get_active_vehicle_types(lavanderia_id=None):
    """Devuelve solo los tipos de vehiculo activos del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(TipoVehiculo)
            .where(
                TipoVehiculo.lavanderia_id == resolved_lavanderia_id,
                TipoVehiculo.estado.is_(True),
            )
            .order_by(TipoVehiculo.nombre.asc())
        )
        return [
            _serialize_vehicle_type(vehicle_type)
            for vehicle_type in session.scalars(query).all()
        ]


def get_vehicle_type_by_id(vehicle_type_id, lavanderia_id=None):
    """Busca un tipo de vehiculo por id dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(TipoVehiculo).where(
            TipoVehiculo.id == vehicle_type_id,
            TipoVehiculo.lavanderia_id == resolved_lavanderia_id,
        )
        vehicle_type = session.scalar(query)
        return (
            _serialize_vehicle_type(vehicle_type)
            if vehicle_type is not None
            else None
        )


def create_vehicle_type(name, lavanderia_id):
    """Inserta un nuevo tipo de vehiculo y devuelve su id."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        vehicle_type = TipoVehiculo(
            nombre=name,
            estado=True,
            lavanderia_id=resolved_lavanderia_id,
        )
        session.add(vehicle_type)
        session.commit()
        return vehicle_type.id


def update_vehicle_type_name(vehicle_type_id, name, lavanderia_id=None):
    """Actualiza el nombre de un tipo de vehiculo."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(TipoVehiculo).where(
            TipoVehiculo.id == vehicle_type_id,
            TipoVehiculo.lavanderia_id == resolved_lavanderia_id,
        )
        vehicle_type = session.scalar(query)
        if vehicle_type is None:
            raise ValueError("El tipo de vehiculo indicado no existe.")

        vehicle_type.nombre = name
        session.commit()


def is_vehicle_type_in_use(vehicle_type_id, lavanderia_id=None):
    """Devuelve True si algun vehiculo referencia este tipo."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Vehiculo.id).where(
            Vehiculo.tipo_vehiculo_id == vehicle_type_id,
            Vehiculo.lavanderia_id == resolved_lavanderia_id,
        ).limit(1)
        return session.scalar(query) is not None


def delete_vehicle_type(vehicle_type_id, lavanderia_id=None):
    """Elimina un tipo de vehiculo permanentemente."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(TipoVehiculo).where(
            TipoVehiculo.id == vehicle_type_id,
            TipoVehiculo.lavanderia_id == resolved_lavanderia_id,
        )
        vehicle_type = session.scalar(query)
        if vehicle_type is None:
            raise ValueError("El tipo de vehiculo indicado no existe.")

        session.delete(vehicle_type)
        session.commit()


def toggle_vehicle_type(vehicle_type_id, lavanderia_id=None):
    """Activa o desactiva un tipo de vehiculo."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(TipoVehiculo).where(
            TipoVehiculo.id == vehicle_type_id,
            TipoVehiculo.lavanderia_id == resolved_lavanderia_id,
        )
        vehicle_type = session.scalar(query)
        if vehicle_type is None:
            raise ValueError("El tipo de vehiculo indicado no existe.")

        vehicle_type.estado = not vehicle_type.estado
        session.commit()
