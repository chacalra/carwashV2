"""Acceso a datos de vehiculos registrados."""

from datetime import datetime

from database.connection import get_connection


def find_vehicle_by_plate(license_plate):
    """Busca un vehiculo por matricula (case-insensitive). Devuelve None si no existe."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                v.id,
                v.license_plate,
                v.vehicle_type_id,
                vt.name AS vehicle_type_name,
                v.owner_name,
                v.phone,
                v.created_at
            FROM vehicles v
            JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            WHERE UPPER(v.license_plate) = UPPER(?);
            """,
            (license_plate,),
        ).fetchone()
        return row
    finally:
        connection.close()


def create_vehicle(license_plate, vehicle_type_id, owner_name=None, phone=None):
    """Inserta un nuevo vehiculo y devuelve su id."""
    connection = get_connection()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            """
            INSERT INTO vehicles (license_plate, vehicle_type_id, owner_name, phone, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (license_plate, vehicle_type_id, owner_name or None, phone or None, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_vehicle(vehicle_id, vehicle_type_id, owner_name=None, phone=None):
    """Actualiza los datos de un vehiculo existente."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE vehicles
            SET vehicle_type_id = ?, owner_name = ?, phone = ?
            WHERE id = ?;
            """,
            (vehicle_type_id, owner_name or None, phone or None, vehicle_id),
        )
        connection.commit()
    finally:
        connection.close()
