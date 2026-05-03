"""Acceso a datos del catalogo de tipos de vehiculo."""

from datetime import datetime

import streamlit as st

from database.connection import get_connection


def get_all_vehicle_types():
    """Devuelve todos los tipos de vehiculo ordenados por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM vehicle_types
            ORDER BY name ASC;
            """
        ).fetchall()
        return rows
    finally:
        connection.close()


@st.cache_data(ttl=60)
def get_active_vehicle_types():
    """Devuelve solo los tipos de vehiculo activos ordenados por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM vehicle_types
            WHERE is_active = 1
            ORDER BY name ASC;
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_vehicle_type_by_id(vehicle_type_id):
    """Busca un tipo de vehiculo por su id."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM vehicle_types
            WHERE id = ?;
            """,
            (vehicle_type_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def create_vehicle_type(name):
    """Inserta un nuevo tipo de vehiculo y devuelve su id."""
    connection = get_connection()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            """
            INSERT INTO vehicle_types (name, is_active, created_at)
            VALUES (?, 1, ?);
            """,
            (name, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_vehicle_type_name(vehicle_type_id, name):
    """Actualiza el nombre de un tipo de vehiculo."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE vehicle_types SET name = ? WHERE id = ?;
            """,
            (name, vehicle_type_id),
        )
        connection.commit()
    finally:
        connection.close()


def is_vehicle_type_in_use(vehicle_type_id):
    """Devuelve True si algun vehiculo referencia este tipo."""
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS c FROM vehicles WHERE vehicle_type_id = ?;", (vehicle_type_id,)
        ).fetchone()
        return row["c"] > 0
    finally:
        connection.close()


def delete_vehicle_type(vehicle_type_id):
    """Elimina un tipo de vehiculo permanentemente."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM vehicle_types WHERE id = ?;", (vehicle_type_id,))
        connection.commit()
    finally:
        connection.close()


def toggle_vehicle_type(vehicle_type_id):
    """Activa o desactiva un tipo de vehiculo."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE vehicle_types
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?;
            """,
            (vehicle_type_id,),
        )
        connection.commit()
    finally:
        connection.close()
