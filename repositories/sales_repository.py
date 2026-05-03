"""Acceso a datos de ventas para la V2."""

from sqlalchemy import func, select

from database.schema import Venta


def list_sales(session, lavanderia_id, start_date=None, end_date=None):
    """Devuelve ventas de una lavanderia ordenadas de mas reciente a mas antigua."""
    query = (
        select(Venta)
        .where(Venta.lavanderia_id == lavanderia_id)
        .order_by(Venta.fecha_venta.desc(), Venta.id.desc())
    )

    if start_date is not None:
        query = query.where(Venta.fecha_venta >= start_date)

    if end_date is not None:
        query = query.where(Venta.fecha_venta <= end_date)

    return session.scalars(query).all()


def get_sale_by_id(session, lavanderia_id, sale_id):
    """Busca una venta por id dentro de una lavanderia."""
    query = select(Venta).where(
        Venta.id == sale_id,
        Venta.lavanderia_id == lavanderia_id,
    )
    return session.scalar(query)


def create_sale(
    session,
    *,
    fecha_venta,
    tipo_cobro,
    total,
    cliente_id,
    lavanderia_id,
    usuario_id,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
):
    """Crea una venta y devuelve la entidad persistida."""
    sale = Venta(
        fecha_venta=fecha_venta,
        tipo_cobro=tipo_cobro,
        metodo_pago=metodo_pago,
        requiere_factura=requiere_factura,
        total=total,
        observacion=observacion,
        cliente_id=cliente_id,
        lavanderia_id=lavanderia_id,
        usuario_id=usuario_id,
        vehiculo_id=vehiculo_id,
    )
    session.add(sale)
    session.flush()
    return sale


def update_sale(
    session,
    sale,
    *,
    fecha_venta,
    tipo_cobro,
    total,
    cliente_id,
    usuario_id,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
):
    """Actualiza los datos principales de una venta."""
    sale.fecha_venta = fecha_venta
    sale.tipo_cobro = tipo_cobro
    sale.metodo_pago = metodo_pago
    sale.requiere_factura = requiere_factura
    sale.total = total
    sale.observacion = observacion
    sale.cliente_id = cliente_id
    sale.usuario_id = usuario_id
    sale.vehiculo_id = vehiculo_id
    session.flush()
    return sale


def delete_sale(session, sale):
    """Elimina una venta."""
    session.delete(sale)
    session.flush()


def get_sales_total_by_period(session, lavanderia_id, start_date, end_date):
    """Calcula el monto total vendido en un rango de fechas."""
    query = select(func.coalesce(func.sum(Venta.total), 0)).where(
        Venta.lavanderia_id == lavanderia_id,
        Venta.fecha_venta >= start_date,
        Venta.fecha_venta <= end_date,
    )
    return session.scalar(query)
