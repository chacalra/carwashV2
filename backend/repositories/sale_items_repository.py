"""Acceso a datos de detalles de venta para la V2."""

from sqlalchemy import select

from backend.database.schema import DetalleVenta


def list_sale_items(session, sale_id):
    """Devuelve los detalles de una venta."""
    query = (
        select(DetalleVenta)
        .where(DetalleVenta.venta_id == sale_id)
        .order_by(DetalleVenta.id.asc())
    )
    return session.scalars(query).all()


def create_sale_item(
    session,
    *,
    venta_id,
    cantidad,
    precio_unitario,
    subtotal,
    servicio_id=None,
    producto_id=None,
):
    """Crea un detalle de venta y devuelve la entidad persistida."""
    item = DetalleVenta(
        venta_id=venta_id,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        subtotal=subtotal,
        servicio_id=servicio_id,
        producto_id=producto_id,
    )
    session.add(item)
    session.flush()
    return item


def create_sale_items(session, sale_id, items):
    """Crea multiples detalles de venta sobre una misma venta."""
    created_items = []

    for item in items:
        created_items.append(
            create_sale_item(
                session,
                venta_id=sale_id,
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"],
                subtotal=item["subtotal"],
                servicio_id=item.get("servicio_id"),
                producto_id=item.get("producto_id"),
            )
        )

    return created_items


def delete_sale_items(session, sale_id):
    """Elimina todos los detalles de una venta."""
    items = list_sale_items(session, sale_id)

    for item in items:
        session.delete(item)

    session.flush()
