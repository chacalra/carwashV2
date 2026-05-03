"""Acceso a datos del catalogo de categorias de egreso para la V2."""

from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import CategoriaEgreso, Egreso
from utils.tenant_context import resolve_lavanderia_id

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


def _serialize_category(category):
    """Convierte una entidad CategoriaEgreso a un diccionario compatible con la UI."""
    return {
        "id": category.id,
        "name": category.nombre_categoria,
        "nombre_categoria": category.nombre_categoria,
        "is_active": 1 if category.estado else 0,
        "estado": category.estado,
        "created_at": category.created_at,
        "lavanderia_id": category.lavanderia_id,
    }


def get_all_categories(lavanderia_id=None):
    """Devuelve todas las categorias del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(CategoriaEgreso)
            .where(CategoriaEgreso.lavanderia_id == resolved_lavanderia_id)
            .order_by(CategoriaEgreso.nombre_categoria.asc())
        )
        return [_serialize_category(category) for category in session.scalars(query).all()]


if st is not None:
    @st.cache_data(ttl=60)
    def get_active_categories(lavanderia_id=None):
        """Devuelve solo las categorias activas del tenant actual."""
        resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

        with SessionLocal() as session:
            query = (
                select(CategoriaEgreso)
                .where(
                    CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
                    CategoriaEgreso.estado.is_(True),
                )
                .order_by(CategoriaEgreso.nombre_categoria.asc())
            )
            return [
                _serialize_category(category)
                for category in session.scalars(query).all()
            ]
else:
    def get_active_categories(lavanderia_id=None):
        """Devuelve solo las categorias activas del tenant actual."""
        resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

        with SessionLocal() as session:
            query = (
                select(CategoriaEgreso)
                .where(
                    CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
                    CategoriaEgreso.estado.is_(True),
                )
                .order_by(CategoriaEgreso.nombre_categoria.asc())
            )
            return [
                _serialize_category(category)
                for category in session.scalars(query).all()
            ]


def get_category_by_id(category_id, lavanderia_id=None):
    """Busca una categoria por id dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(CategoriaEgreso).where(
            CategoriaEgreso.id == category_id,
            CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
        )
        category = session.scalar(query)
        return _serialize_category(category) if category is not None else None


def create_category(name, lavanderia_id):
    """Inserta una nueva categoria y devuelve su id."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        category = CategoriaEgreso(
            nombre_categoria=name,
            estado=True,
            lavanderia_id=resolved_lavanderia_id,
        )
        session.add(category)
        session.commit()
        return category.id


def update_category_name(category_id, name, lavanderia_id=None):
    """Actualiza el nombre de una categoria."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(CategoriaEgreso).where(
            CategoriaEgreso.id == category_id,
            CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
        )
        category = session.scalar(query)
        if category is None:
            raise ValueError("La categoria indicada no existe.")

        category.nombre_categoria = name
        session.commit()


def is_category_in_use(category_id, lavanderia_id=None):
    """Devuelve True si algun egreso referencia esta categoria."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Egreso.id).where(
            Egreso.categoria_egreso_id == category_id,
            Egreso.lavanderia_id == resolved_lavanderia_id,
        ).limit(1)
        return session.scalar(query) is not None


def delete_category(category_id, lavanderia_id=None):
    """Elimina una categoria permanentemente."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(CategoriaEgreso).where(
            CategoriaEgreso.id == category_id,
            CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
        )
        category = session.scalar(query)
        if category is None:
            raise ValueError("La categoria indicada no existe.")

        session.delete(category)
        session.commit()


def toggle_category(category_id, lavanderia_id=None):
    """Activa o desactiva una categoria."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(CategoriaEgreso).where(
            CategoriaEgreso.id == category_id,
            CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
        )
        category = session.scalar(query)
        if category is None:
            raise ValueError("La categoria indicada no existe.")

        category.estado = not category.estado
        session.commit()
