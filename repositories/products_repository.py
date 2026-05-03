"""Acceso a datos del catalogo de productos."""

from datetime import datetime

import streamlit as st

from database.connection import get_connection


def get_all_products():
    """Devuelve todos los productos ordenados por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM products
            ORDER BY name ASC;
            """
        ).fetchall()
        return rows
    finally:
        connection.close()


@st.cache_data(ttl=60)
def get_active_products():
    """Devuelve solo los productos activos ordenados por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM products
            WHERE is_active = 1
            ORDER BY name ASC;
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_product_by_id(product_id):
    """Busca un producto por su id."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM products
            WHERE id = ?;
            """,
            (product_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def create_product(name):
    """Inserta un nuevo producto y devuelve su id."""
    connection = get_connection()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            """
            INSERT INTO products (name, is_active, created_at)
            VALUES (?, 1, ?);
            """,
            (name, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_product_name(product_id, name):
    """Actualiza el nombre de un producto."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE products SET name = ? WHERE id = ?;
            """,
            (name, product_id),
        )
        connection.commit()
    finally:
        connection.close()


def is_product_in_use(product_id):
    """Devuelve True si algun ingreso referencia este producto."""
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS c FROM incomes WHERE product_id = ?;", (product_id,)
        ).fetchone()
        return row["c"] > 0
    finally:
        connection.close()


def delete_product(product_id):
    """Elimina un producto permanentemente."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM products WHERE id = ?;", (product_id,))
        connection.commit()
    finally:
        connection.close()


def toggle_product(product_id):
    """Activa o desactiva un producto."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE products
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?;
            """,
            (product_id,),
        )
        connection.commit()
    finally:
        connection.close()
