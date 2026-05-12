"""Reglas de negocio para vehiculos y matriculas."""

from backend.repositories.vehicle_types_repository import get_vehicle_type_by_id
from backend.repositories.vehicles_repository import (
    create_vehicle,
    find_vehicle_by_plate,
    get_vehicle_by_id,
    list_vehicles as repo_list_vehicles,
    set_vehicle_status,
    update_vehicle,
)
from backend.utils.tenant_context import resolve_lavanderia_id


def normalize_plate(plate):
    """Normaliza una matricula: mayusculas y sin espacios extra."""
    if not isinstance(plate, str):
        raise ValueError("La matricula del vehiculo es obligatoria.")

    normalized = plate.strip().upper()
    if not normalized:
        raise ValueError("La matricula del vehiculo es obligatoria.")

    return normalized


def _clean_optional_text(value):
    """Normaliza un texto opcional a string sin espacios o None."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_vehicle_type(vehicle_type_id, lavanderia_id):
    """Verifica que el tipo de vehiculo exista y este activo."""
    vehicle_type = get_vehicle_type_by_id(vehicle_type_id, lavanderia_id=lavanderia_id)
    if vehicle_type is None:
        raise ValueError("El tipo de vehiculo seleccionado no existe.")
    if not vehicle_type["estado"]:
        raise ValueError("No se puede usar un tipo de vehiculo inactivo.")
    return vehicle_type


def find_or_create_vehicle(
    license_plate,
    vehicle_type_id,
    owner_name=None,
    phone=None,
    lavanderia_id=None,
):
    """
    Busca un vehiculo por matricula y lo actualiza, o crea uno nuevo si no existe.
    Devuelve el id del vehiculo.
    """
    target_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    normalized_plate = normalize_plate(license_plate)
    _validate_vehicle_type(vehicle_type_id, target_lavanderia_id)

    existing = find_vehicle_by_plate(normalized_plate, lavanderia_id=target_lavanderia_id)

    normalized_owner = _clean_optional_text(owner_name)
    normalized_phone = _clean_optional_text(phone)

    if existing:
        merged_owner = normalized_owner if normalized_owner is not None else existing.get("owner_name")
        merged_phone = normalized_phone if normalized_phone is not None else existing.get("phone")
        update_vehicle(
            existing["id"],
            vehicle_type_id,
            merged_owner,
            merged_phone,
            lavanderia_id=target_lavanderia_id,
        )
        return existing["id"]

    return create_vehicle(
        normalized_plate,
        vehicle_type_id,
        normalized_owner,
        normalized_phone,
        lavanderia_id=target_lavanderia_id,
    )


def get_vehicle(vehicle_id, lavanderia_id=None):
    """Devuelve un vehiculo por id o None si no existe."""
    target = resolve_lavanderia_id(lavanderia_id, required=True)
    return get_vehicle_by_id(vehicle_id, lavanderia_id=target)


def list_vehicles(lavanderia_id=None, *, only_active=True, search=None):
    """Lista vehiculos del tenant con filtros opcionales."""
    target = resolve_lavanderia_id(lavanderia_id, required=True)
    return repo_list_vehicles(target, only_active=only_active, search=search)


def edit_vehicle(vehicle_id, vehicle_type_id, owner_name=None, phone=None, lavanderia_id=None):
    """Valida y actualiza los datos de un vehiculo existente."""
    target = resolve_lavanderia_id(lavanderia_id, required=True)
    _validate_vehicle_type(vehicle_type_id, target)

    existing = get_vehicle_by_id(vehicle_id, lavanderia_id=target)
    if existing is None:
        raise ValueError("El vehiculo indicado no existe.")

    normalized_owner = _clean_optional_text(owner_name)
    normalized_phone = _clean_optional_text(phone)
    update_vehicle(vehicle_id, vehicle_type_id, normalized_owner, normalized_phone, lavanderia_id=target)
    return vehicle_id


def toggle_vehicle_status(vehicle_id, active, lavanderia_id=None):
    """Activa o desactiva un vehiculo."""
    target = resolve_lavanderia_id(lavanderia_id, required=True)
    set_vehicle_status(vehicle_id, active, lavanderia_id=target)
