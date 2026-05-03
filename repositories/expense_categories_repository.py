"""Acceso a datos del catalogo de categorias de egreso."""

from datetime import datetime

import streamlit as st

from database.connection import get_connection


def get_all_categories():
    """Devuelve todas las categorias ordenadas por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM expense_categories
            ORDER BY name ASC;
            """
        ).fetchall()
        return rows
    finally:
        connection.close()


@st.cache_data(ttl=60)
def get_active_categories():
    """Devuelve solo las categorias activas ordenadas por nombre."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM expense_categories
            WHERE is_active = 1
            ORDER BY name ASC;
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_category_by_id(category_id):
    """Busca una categoria por su id."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT id, name, is_active, created_at
            FROM expense_categories
            WHERE id = ?;
            """,
            (category_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def create_category(name):
    """Inserta una nueva categoria y devuelve su id."""
    connection = get_connection()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = connection.execute(
            """
            INSERT INTO expense_categories (name, is_active, created_at)
            VALUES (?, 1, ?);
            """,
            (name, created_at),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_category_name(category_id, name):
    """Actualiza el nombre de una categoria."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE expense_categories SET name = ? WHERE id = ?;
            """,
            (name, category_id),
        )
        connection.commit()
    finally:
        connection.close()


def is_category_in_use(category_id):
    """Devuelve True si algun egreso referencia esta categoria."""
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS c FROM expenses WHERE category_id = ?;", (category_id,)
        ).fetchone()
        return row["c"] > 0
    finally:
        connection.close()


def delete_category(category_id):
    """Elimina una categoria permanentemente."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM expense_categories WHERE id = ?;", (category_id,))
        connection.commit()
    finally:
        connection.close()


def toggle_category(category_id):
    """Activa o desactiva una categoria."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE expense_categories
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
            WHERE id = ?;
            """,
            (category_id,),
        )
        connection.commit()
    finally:
        connection.close()
