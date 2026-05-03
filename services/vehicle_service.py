"""Reglas de negocio para vehiculos y matriculas."""

from repositories.vehicles_repository import (
    create_vehicle,
    find_vehicle_by_plate,
    update_vehicle,
)


def normalize_plate(plate):
    """Normaliza una matricula: mayusculas y sin espacios extra."""
    return plate.strip().upper()


def find_or_create_vehicle(license_plate, vehicle_type_id, owner_name=None, phone=None):
    """
    Busca un vehiculo por matricula y lo actualiza, o crea uno nuevo si no existe.
    Devuelve el id del vehiculo.
    """
    normalized = normalize_plate(license_plate)
    existing = find_vehicle_by_plate(normalized)

    normalized_owner = owner_name.strip() if isinstance(owner_name, str) and owner_name.strip() else None
    normalized_phone = phone.strip() if isinstance(phone, str) and phone.strip() else None

    if existing:
        merged_owner = normalized_owner if normalized_owner is not None else existing["owner_name"]
        merged_phone = normalized_phone if normalized_phone is not None else existing["phone"]
        update_vehicle(existing["id"], vehicle_type_id, merged_owner, merged_phone)
        return existing["id"]

    return create_vehicle(normalized, vehicle_type_id, normalized_owner, normalized_phone)
