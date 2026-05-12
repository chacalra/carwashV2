"""Acceso a datos del catalogo de productos para la V2."""

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import DetalleVenta, Producto
from backend.utils.tenant_context import resolve_lavanderia_id


def _serialize_product(product):
    """Convierte una entidad Producto a un diccionario compatible con la UI actual."""
    return {
        "id": product.id,
        "name": product.nombre_producto,
        "nombre_producto": product.nombre_producto,
        "price": product.precio,
        "precio": product.precio,
        "is_active": 1 if product.estado else 0,
        "estado": product.estado,
        "created_at": product.created_at,
        "lavanderia_id": product.lavanderia_id,
    }


def get_all_products(lavanderia_id=None):
    """Devuelve todos los productos del tenant actual ordenados por nombre."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(Producto)
            .where(Producto.lavanderia_id == resolved_lavanderia_id)
            .order_by(Producto.nombre_producto.asc())
        )
        return [_serialize_product(product) for product in session.scalars(query).all()]


def get_active_products(lavanderia_id=None):
    """Devuelve solo los productos activos del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(Producto)
            .where(
                Producto.lavanderia_id == resolved_lavanderia_id,
                Producto.estado.is_(True),
            )
            .order_by(Producto.nombre_producto.asc())
        )
        return [_serialize_product(product) for product in session.scalars(query).all()]


def get_product_by_id(product_id, lavanderia_id=None):
    """Busca un producto por id dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Producto).where(
            Producto.id == product_id,
            Producto.lavanderia_id == resolved_lavanderia_id,
        )
        product = session.scalar(query)
        return _serialize_product(product) if product is not None else None


def create_product(name, lavanderia_id, price=0):
    """Inserta un nuevo producto y devuelve su id."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        product = Producto(
            nombre_producto=name,
            precio=price,
            estado=True,
            lavanderia_id=resolved_lavanderia_id,
        )
        session.add(product)
        session.commit()
        return product.id


def update_product(product_id, name=None, price=None, lavanderia_id=None):
    """Actualiza nombre y/o precio de un producto."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Producto).where(
            Producto.id == product_id,
            Producto.lavanderia_id == resolved_lavanderia_id,
        )
        product = session.scalar(query)
        if product is None:
            raise ValueError("El producto indicado no existe.")

        if name is not None:
            product.nombre_producto = name
        if price is not None:
            product.precio = price
        session.commit()


def update_product_name(product_id, name, lavanderia_id=None):
    """Actualiza solo el nombre de un producto."""
    update_product(product_id, name=name, lavanderia_id=lavanderia_id)


def is_product_in_use(product_id, lavanderia_id=None):
    """Devuelve True si algun detalle de venta referencia este producto."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(DetalleVenta.id)
            .join(Producto, Producto.id == DetalleVenta.producto_id)
            .where(
                DetalleVenta.producto_id == product_id,
                Producto.lavanderia_id == resolved_lavanderia_id,
            )
            .limit(1)
        )
        return session.scalar(query) is not None


def delete_product(product_id, lavanderia_id=None):
    """Elimina un producto permanentemente."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Producto).where(
            Producto.id == product_id,
            Producto.lavanderia_id == resolved_lavanderia_id,
        )
        product = session.scalar(query)
        if product is None:
            raise ValueError("El producto indicado no existe.")

        session.delete(product)
        session.commit()


def toggle_product(product_id, lavanderia_id=None):
    """Activa o desactiva un producto."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(Producto).where(
            Producto.id == product_id,
            Producto.lavanderia_id == resolved_lavanderia_id,
        )
        product = session.scalar(query)
        if product is None:
            raise ValueError("El producto indicado no existe.")

        product.estado = not product.estado
        session.commit()
