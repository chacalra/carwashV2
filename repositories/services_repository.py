"""Acceso a datos del catalogo de servicios."""

from datetime import datetime

import streamlit as st

from database.connection import get_connection


def get_all_services():
    """Devuelve todos los servicios ordenados por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM services
            ORDER BY name ASC;
            """
        ).fetchall()
        return rows
    finally:
        connection.close()


@st.cache_data(ttl=60)
def get_active_services():
    """Devuelve solo los servicios activos ordenados por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM services
            WHERE is_active = 1
            ORDER BY name ASC;
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_service_by_id(service_id):
    """Busca un servicio por su id."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM services
            WHERE id = ?;
            """,
            (service_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def create_service(name):
    """Inserta un nuevo servicio y devuelve su id."""
    connection = get_connection()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            """
            INSERT INTO services (name, is_active, created_at)
            VALUES (?, 1, ?);
            """,
            (name, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_service_name(service_id, name):
    """Actualiza el nombre de un servicio."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE services SET name = ? WHERE id = ?;
            """,
            (name, service_id),
        )
        connection.commit()
    finally:
        connection.close()


def is_service_in_use(service_id):
    """Devuelve True si algun ingreso referencia este servicio."""
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS c FROM incomes WHERE service_id = ?;", (service_id,)
        ).fetchone()
        return row["c"] > 0
    finally:
        connection.close()


def delete_service(service_id):
    """Elimina un servicio permanentemente."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM services WHERE id = ?;", (service_id,))
        connection.commit()
    finally:
        connection.close()


def toggle_service(service_id):
    """Activa o desactiva un servicio."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE services
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?;
            """,
            (service_id,),
        )
        connection.commit()
    finally:
        connection.close()
