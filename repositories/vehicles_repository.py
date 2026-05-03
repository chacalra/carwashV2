"""Acceso a datos de vehiculos para la V2."""

from sqlalchemy import func, select

from database.connection import SessionLocal
from database.schema import Cliente, TipoVehiculo, Vehiculo
from utils.tenant_context import resolve_lavanderia_id


def _clean_optional_text(value):
    """Normaliza un texto opcional a string sin espacios o None."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _serialize_vehicle(vehicle, vehicle_type=None, client=None):
    """Convierte una entidad Vehiculo a un diccionario compatible con la UI actual."""
    resolved_vehicle_type = vehicle_type
    resolved_client = client

    return {
        "id": vehicle.id,
        "license_plate": vehicle.matricula,
        "matricula": vehicle.matricula,
        "vehicle_type_id": vehicle.tipo_vehiculo_id,
        "tipo_vehiculo_id": vehicle.tipo_vehiculo_id,
        "vehicle_type_name": resolved_vehicle_type.nombre if resolved_vehicle_type is not None else None,
        "vehicle_type": resolved_vehicle_type.nombre if resolved_vehicle_type is not None else None,
        "owner_name": resolved_client.nombre if resolved_client is not None else None,
        "phone": resolved_client.telefono if resolved_client is not None else None,
        "client_id": vehicle.cliente_id,
        "cliente_id": vehicle.cliente_id,
        "is_active": 1 if vehicle.estado else 0,
        "estado": vehicle.estado,
        "created_at": vehicle.created_at,
        "lavanderia_id": vehicle.lavanderia_id,
    }


def _resolve_vehicle_type(session, vehicle_type_id, lavanderia_id):
    """Busca y valida un tipo de vehiculo dentro de una lavanderia."""
    query = select(TipoVehiculo).where(
        TipoVehiculo.id == vehicle_type_id,
        TipoVehiculo.lavanderia_id == lavanderia_id,
    )
    vehicle_type = session.scalar(query)
    if vehicle_type is None:
        raise ValueError("El tipo de vehiculo indicado no existe.")
    return vehicle_type


def _resolve_client(session, lavanderia_id, *, client_id=None, owner_name=None, phone=None):
    """Resuelve o crea un cliente puente para conservar compatibilidad con la UI heredada."""
    if client_id is not None:
        query = select(Cliente).where(
            Cliente.id == client_id,
            Cliente.lavanderia_id == lavanderia_id,
        )
        client = session.scalar(query)
        if client is None:
            raise ValueError("El cliente indicado no existe.")
        return client

    clean_owner = _clean_optional_text(owner_name)
    clean_phone = _clean_optional_text(phone)

    if clean_owner is None and clean_phone is None:
        return None

    if clean_owner is None:
        return None

    query = select(Cliente).where(
        Cliente.lavanderia_id == lavanderia_id,
        Cliente.tipo_cliente == "particular",
        func.lower(Cliente.nombre) == clean_owner.lower(),
        Cliente.telefono == clean_phone,
    )
    existing = session.scalar(query)
    if existing is not None:
        return existing

    client = Cliente(
        nombre=clean_owner,
        tipo_cliente="particular",
        telefono=clean_phone,
        estado=True,
        lavanderia_id=lavanderia_id,
    )
    session.add(client)
    session.flush()
    return client


def find_vehicle_by_plate(license_plate, lavanderia_id=None):
    """Busca un vehiculo por matricula dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    clean_plate = _clean_optional_text(license_plate)
    if clean_plate is None:
        return None

    with SessionLocal() as session:
        query = (
            select(Vehiculo, TipoVehiculo, Cliente)
            .join(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
            .outerjoin(Cliente, Cliente.id == Vehiculo.cliente_id)
            .where(
                Vehiculo.lavanderia_id == resolved_lavanderia_id,
                func.upper(Vehiculo.matricula) == clean_plate.upper(),
            )
            .order_by(Vehiculo.id.asc())
        )
        row = session.execute(query).first()
        if row is None:
            return None

        vehicle, vehicle_type, client = row
        return _serialize_vehicle(vehicle, vehicle_type, client)


def create_vehicle(
    license_plate,
    vehicle_type_id,
    owner_name=None,
    phone=None,
    *,
    lavanderia_id=None,
    client_id=None,
):
    """Inserta un nuevo vehiculo y devuelve su id."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    clean_plate = _clean_optional_text(license_plate)

    with SessionLocal() as session:
        _resolve_vehicle_type(session, vehicle_type_id, resolved_lavanderia_id)
        client = _resolve_client(
            session,
            resolved_lavanderia_id,
            client_id=client_id,
            owner_name=owner_name,
            phone=phone,
        )

        vehicle = Vehiculo(
            matricula=clean_plate,
            estado=True,
            lavanderia_id=resolved_lavanderia_id,
            tipo_vehiculo_id=vehicle_type_id,
            cliente_id=client.id if client is not None else None,
        )
        session.add(vehicle)
        session.commit()
        return vehicle.id


def update_vehicle(
    vehicle_id,
    vehicle_type_id,
    owner_name=None,
    phone=None,
    *,
    lavanderia_id=None,
    client_id=None,
):
    """Actualiza los datos principales de un vehiculo existente."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Vehiculo).where(
            Vehiculo.id == vehicle_id,
            Vehiculo.lavanderia_id == resolved_lavanderia_id,
        )
        vehicle = session.scalar(query)
        if vehicle is None:
            raise ValueError("El vehiculo indicado no existe.")

        _resolve_vehicle_type(session, vehicle_type_id, resolved_lavanderia_id)

        current_client = None
        if vehicle.cliente_id is not None:
            current_client = session.get(Cliente, vehicle.cliente_id)

        if client_id is not None:
            resolved_client = _resolve_client(
                session,
                resolved_lavanderia_id,
                client_id=client_id,
            )
        elif current_client is not None:
            clean_owner = _clean_optional_text(owner_name)
            clean_phone = _clean_optional_text(phone)
            current_client.nombre = clean_owner or current_client.nombre
            current_client.telefono = clean_phone
            resolved_client = current_client
        else:
            resolved_client = _resolve_client(
                session,
                resolved_lavanderia_id,
                owner_name=owner_name,
                phone=phone,
            )

        vehicle.tipo_vehiculo_id = vehicle_type_id
        vehicle.cliente_id = resolved_client.id if resolved_client is not None else None
        session.commit()
