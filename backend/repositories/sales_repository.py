"""Acceso a datos de ventas para la V2."""

from datetime import date as date_type

from sqlalchemy import func, select

from backend.database.connection import SessionLocal
from backend.database.schema import (
    Cliente,
    DetalleVenta,
    Producto,
    Servicio,
    TipoVehiculo,
    Usuario,
    Vehiculo,
    Venta,
)
from backend.utils.tenant_context import resolve_lavanderia_id


def _parse_date_like(value):
    """Convierte strings YYYY-MM-DD u objetos date a un date real."""
    if isinstance(value, date_type):
        return value
    if isinstance(value, str):
        return date_type.fromisoformat(value.strip())
    raise ValueError("La fecha indicada no es valida.")


def list_sales(session, lavanderia_id, start_date=None, end_date=None):
    """Devuelve ventas activas de una lavanderia ordenadas de mas reciente a mas antigua."""
    query = (
        select(Venta)
        .where(Venta.lavanderia_id == lavanderia_id, Venta.estado == True)  # noqa: E712
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
    """Elimina una venta fisicamente."""
    session.delete(sale)
    session.flush()


def void_sale(session, sale):
    """Anula una venta de forma logica."""
    sale.estado = False
    session.flush()


def get_sales_total_by_period(start_date, end_date, lavanderia_id=None):
    """Calcula el monto total vendido en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.coalesce(func.sum(DetalleVenta.subtotal), 0)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.estado == True,  # noqa: E712
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
        )
        total = session.scalar(query)
        return float(total or 0)


def get_sales_breakdown_by_item(start_date, end_date, lavanderia_id=None):
    """Agrupa ventas por servicio o producto para un periodo dado."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        name_expr = func.coalesce(Servicio.nombre_servicio, Producto.nombre_producto)
        query = (
            select(
                name_expr.label("name"),
                func.count(DetalleVenta.id).label("count"),
                func.coalesce(func.sum(DetalleVenta.subtotal), 0).label("total"),
            )
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .outerjoin(Servicio, Servicio.id == DetalleVenta.servicio_id)
            .outerjoin(Producto, Producto.id == DetalleVenta.producto_id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.estado == True,  # noqa: E712
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
            )
            .group_by(name_expr)
            .order_by(func.sum(DetalleVenta.subtotal).desc())
        )
        rows = session.execute(query).all()
        return [
            {"name": name, "count": count, "total": float(total)}
            for name, count, total in rows
        ]


def get_service_sales_count_by_period(start_date, end_date, lavanderia_id=None):
    """Cuenta servicios vendidos en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.count(DetalleVenta.id)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.estado == True,  # noqa: E712
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
            DetalleVenta.servicio_id.is_not(None),
        )
        return session.scalar(query) or 0


def get_product_sales_count_by_period(start_date, end_date, lavanderia_id=None):
    """Cuenta lineas de productos vendidas en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.count(DetalleVenta.id)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.estado == True,  # noqa: E712
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
            DetalleVenta.producto_id.is_not(None),
        )
        return session.scalar(query) or 0


def get_service_sales_total_by_period(start_date, end_date, lavanderia_id=None):
    """Calcula el total vendido en servicios en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.coalesce(func.sum(DetalleVenta.subtotal), 0)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.estado == True,  # noqa: E712
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
            DetalleVenta.servicio_id.is_not(None),
        )
        total = session.scalar(query)
        return float(total or 0)


def get_sales_total_by_payment_type(start_date, end_date, lavanderia_id=None):
    """Devuelve totales vendidos separados por tipo de cobro."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        payment_type_expr = func.coalesce(Venta.tipo_cobro, "Contado")
        query = (
            select(
                payment_type_expr.label("payment_type"),
                func.coalesce(func.sum(DetalleVenta.subtotal), 0).label("total"),
            )
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.estado == True,  # noqa: E712
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
            )
            .group_by(payment_type_expr)
        )
        rows = session.execute(query).all()
        return {payment_type: float(total) for payment_type, total in rows}


def get_product_sales_stats(start_date, end_date, lavanderia_id=None):
    """Devuelve estadisticas de ventas por producto para un periodo."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(
                Producto.nombre_producto.label("name"),
                func.count(DetalleVenta.id).label("sale_count"),
                func.coalesce(func.sum(DetalleVenta.subtotal), 0).label("total"),
            )
            .join(Producto, Producto.id == DetalleVenta.producto_id)
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.estado == True,  # noqa: E712
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
                DetalleVenta.producto_id.is_not(None),
            )
            .group_by(Producto.id, Producto.nombre_producto)
            .order_by(func.count(DetalleVenta.id).desc())
        )
        rows = session.execute(query).all()
        return [
            {"name": name, "sale_count": sale_count, "total": float(total)}
            for name, sale_count, total in rows
        ]


def get_vehicle_sales_stats(start_date, end_date, lavanderia_id=None):
    """Devuelve estadisticas de vehiculos atendidos en un periodo."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(
                Vehiculo.matricula.label("license_plate"),
                TipoVehiculo.nombre.label("vehicle_type"),
                Cliente.nombre.label("owner_name"),
                func.count(Venta.id).label("visit_count"),
            )
            .join(Venta, Venta.vehiculo_id == Vehiculo.id)
            .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
            .outerjoin(Cliente, Cliente.id == Vehiculo.cliente_id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.estado == True,  # noqa: E712
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
                ~Vehiculo.matricula.in_(("9999", "0000")),
            )
            .group_by(Vehiculo.id, Vehiculo.matricula, TipoVehiculo.nombre, Cliente.nombre)
            .order_by(func.count(Venta.id).desc())
        )
        rows = session.execute(query).all()
        return [
            {
                "license_plate": license_plate,
                "vehicle_type": vehicle_type,
                "owner_name": owner_name,
                "visit_count": visit_count,
            }
            for license_plate, vehicle_type, owner_name, visit_count in rows
        ]


def get_daily_sales(start_date, end_date, lavanderia_id=None):
    """Devuelve ventas totales agrupadas por dia para el periodo dado."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(
                Venta.fecha_venta.label("date"),
                func.coalesce(func.sum(DetalleVenta.subtotal), 0).label("total"),
            )
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.estado == True,  # noqa: E712
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
            )
            .group_by(Venta.fecha_venta)
            .order_by(Venta.fecha_venta.asc())
        )
        rows = session.execute(query).all()
        return [{"date": row.date, "total": float(row.total)} for row in rows]


def get_sales_export_rows(start_date=None, end_date=None, lavanderia_id=None):
    """Devuelve filas de ventas y detalles para exportacion."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        item_name = func.coalesce(Servicio.nombre_servicio, Producto.nombre_producto)
        query = (
            select(
                Venta.id.label("sale_id"),
                Venta.fecha_venta.label("date"),
                Venta.tipo_cobro.label("payment_type"),
                Venta.metodo_pago.label("payment_method"),
                Venta.requiere_factura.label("requires_invoice"),
                Cliente.nombre.label("customer_name"),
                Cliente.ruc_ci.label("ruc_ci"),
                Vehiculo.matricula.label("license_plate"),
                TipoVehiculo.nombre.label("vehicle_type"),
                item_name.label("item"),
                DetalleVenta.cantidad.label("quantity"),
                DetalleVenta.precio_unitario.label("unit_price"),
                DetalleVenta.subtotal.label("subtotal"),
                Venta.total.label("sale_total"),
                Usuario.nombre_usuario.label("created_by"),
                Venta.observacion.label("notes"),
                DetalleVenta.servicio_id.label("service_id"),
                DetalleVenta.producto_id.label("product_id"),
            )
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .join(Cliente, Cliente.id == Venta.cliente_id)
            .join(Usuario, Usuario.id == Venta.usuario_id)
            .outerjoin(Servicio, Servicio.id == DetalleVenta.servicio_id)
            .outerjoin(Producto, Producto.id == DetalleVenta.producto_id)
            .outerjoin(Vehiculo, Vehiculo.id == Venta.vehiculo_id)
            .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
            .where(Venta.lavanderia_id == resolved_lavanderia_id)
        )

        query = query.where(Venta.estado == True)  # noqa: E712

        if start_date and end_date:
            query = query.where(
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                )
            )

        rows = session.execute(
            query.order_by(Venta.fecha_venta.desc(), Venta.id.desc(), DetalleVenta.id.asc())
        ).all()
        return [
            {
                "sale_id": row.sale_id,
                "date": row.date,
                "payment_type": row.payment_type,
                "payment_method": row.payment_method,
                "requires_invoice": row.requires_invoice,
                "customer_name": row.customer_name,
                "ruc_ci": row.ruc_ci,
                "license_plate": row.license_plate,
                "vehicle_type": row.vehicle_type,
                "item_type": "Servicio" if row.service_id is not None else "Producto",
                "item": row.item,
                "quantity": row.quantity,
                "unit_price": float(row.unit_price),
                "subtotal": float(row.subtotal),
                "sale_total": float(row.sale_total),
                "created_by": row.created_by,
                "notes": row.notes,
            }
            for row in rows
        ]


def _sales_grouped_query(lavanderia_id):
    """Builds the grouped sales query with customer, vehicle and detail data."""
    item_name = func.coalesce(Servicio.nombre_servicio, Producto.nombre_producto)
    return (
        select(
            Venta.id.label("sale_id"),
            Venta.fecha_venta.label("date"),
            Venta.created_at.label("created_at"),
            Venta.tipo_cobro.label("payment_type"),
            Venta.metodo_pago.label("payment_method"),
            Venta.requiere_factura.label("requires_invoice"),
            Venta.total.label("total"),
            Venta.observacion.label("notes"),
            Venta.estado.label("is_active"),
            Venta.cliente_id.label("customer_id"),
            Cliente.nombre.label("customer_name"),
            Cliente.ruc_ci.label("ruc_ci"),
            Venta.vehiculo_id.label("vehicle_id"),
            Vehiculo.matricula.label("license_plate"),
            TipoVehiculo.id.label("vehicle_type_id"),
            TipoVehiculo.nombre.label("vehicle_type_name"),
            Venta.usuario_id.label("created_by_user_id"),
            Usuario.nombre_usuario.label("created_by"),
            Venta.lavanderia_id.label("lavanderia_id"),
            DetalleVenta.id.label("item_id"),
            DetalleVenta.servicio_id.label("service_id"),
            DetalleVenta.producto_id.label("product_id"),
            item_name.label("item_name"),
            DetalleVenta.cantidad.label("quantity"),
            DetalleVenta.precio_unitario.label("unit_price"),
            DetalleVenta.subtotal.label("subtotal"),
        )
        .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        .join(Cliente, Cliente.id == Venta.cliente_id)
        .join(Usuario, Usuario.id == Venta.usuario_id)
        .outerjoin(Servicio, Servicio.id == DetalleVenta.servicio_id)
        .outerjoin(Producto, Producto.id == DetalleVenta.producto_id)
        .outerjoin(Vehiculo, Vehiculo.id == Venta.vehiculo_id)
        .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
        .where(Venta.lavanderia_id == lavanderia_id)
    )


def _group_sales_rows(rows):
    """Groups joined sales/detail rows into sale documents."""
    grouped_sales = []
    current_sale = None
    current_sale_id = None

    for row in rows:
        if row.sale_id != current_sale_id:
            current_sale = {
                "id": row.sale_id,
                "date": row.date,
                "created_at": row.created_at,
                "payment_type": row.payment_type,
                "payment_method": row.payment_method,
                "requires_invoice": row.requires_invoice,
                "total": float(row.total),
                "notes": row.notes,
                "is_voided": not row.is_active,
                "customer_id": row.customer_id,
                "customer_name": row.customer_name,
                "ruc_ci": row.ruc_ci,
                "vehicle_id": row.vehicle_id,
                "license_plate": row.license_plate,
                "vehicle_type_id": row.vehicle_type_id,
                "vehicle_type_name": row.vehicle_type_name,
                "created_by_user_id": row.created_by_user_id,
                "created_by": row.created_by,
                "lavanderia_id": row.lavanderia_id,
                "items": [],
            }
            grouped_sales.append(current_sale)
            current_sale_id = row.sale_id

        current_sale["items"].append(
            {
                "id": row.item_id,
                "item_type": "Servicio" if row.service_id is not None else "Producto",
                "item_name": row.item_name,
                "service_id": row.service_id,
                "product_id": row.product_id,
                "quantity": row.quantity,
                "unit_price": float(row.unit_price),
                "subtotal": float(row.subtotal),
            }
        )

    return grouped_sales


def get_sales_grouped(start_date=None, end_date=None, lavanderia_id=None):
    """Returns grouped sales documents with nested detail lines."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = _sales_grouped_query(resolved_lavanderia_id).where(Venta.estado == True)  # noqa: E712

        if start_date is not None:
            query = query.where(Venta.fecha_venta >= _parse_date_like(start_date))
        if end_date is not None:
            query = query.where(Venta.fecha_venta <= _parse_date_like(end_date))

        rows = session.execute(
            query.order_by(Venta.fecha_venta.desc(), Venta.id.desc(), DetalleVenta.id.asc())
        ).all()
        return _group_sales_rows(rows)


def get_grouped_sale_by_id(sale_id, lavanderia_id=None):
    """Returns one grouped sale document or None if it does not exist."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = _sales_grouped_query(resolved_lavanderia_id).where(Venta.id == sale_id)
        rows = session.execute(
            query.order_by(Venta.id.asc(), DetalleVenta.id.asc())
        ).all()

    grouped_sales = _group_sales_rows(rows)
    if not grouped_sales:
        return None
    return grouped_sales[0]
