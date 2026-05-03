"""Acceso a datos de ingresos legacy sobre el modelo V2."""

from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from database.connection import SessionLocal
from database.schema import (
    Cliente,
    DetalleVenta,
    Producto,
    Servicio,
    TipoVehiculo,
    Usuario,
    Vehiculo,
    Venta,
)
from repositories.clients_repository import create_client, get_client_by_ruc_ci, get_generic_client
from repositories.sale_items_repository import create_sale_item, delete_sale_items
from repositories.sales_repository import create_sale, delete_sale, get_sale_by_id, update_sale
from utils.formatters import is_company_name
from utils.tenant_context import resolve_lavanderia_id


def _parse_date_like(value):
    """Convierte strings YYYY-MM-DD u objetos date a un date real."""
    if isinstance(value, date_type):
        return value
    if isinstance(value, str):
        return date_type.fromisoformat(value.strip())
    raise ValueError("La fecha indicada no es valida.")


def _clean_optional_text(value):
    """Normaliza un texto opcional a string sin espacios o None."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _to_decimal_amount(amount):
    """Convierte un monto a Decimal con dos decimales."""
    return Decimal(str(amount)).quantize(Decimal("0.01"))


def _resolve_user(session, lavanderia_id, *, user_id=None, created_by=None, fallback_user_id=None):
    """Resuelve el usuario asociado a la venta."""
    target_user_id = user_id if user_id is not None else fallback_user_id
    if target_user_id is not None:
        query = select(Usuario).where(
            Usuario.id == target_user_id,
            Usuario.lavanderia_id == lavanderia_id,
        )
        user = session.scalar(query)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        return user

    if isinstance(created_by, str) and created_by.strip():
        query = select(Usuario).where(
            Usuario.nombre_usuario == created_by.strip(),
            Usuario.lavanderia_id == lavanderia_id,
        )
        user = session.scalar(query)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        return user

    raise ValueError("Hace falta indicar el usuario que registra el ingreso.")


def _resolve_vehicle(session, lavanderia_id, vehicle_id):
    """Valida el vehiculo opcional asociado a la venta."""
    if vehicle_id is None:
        return None

    query = select(Vehiculo).where(
        Vehiculo.id == vehicle_id,
        Vehiculo.lavanderia_id == lavanderia_id,
    )
    vehicle = session.scalar(query)
    if vehicle is None:
        raise ValueError("El vehiculo indicado no existe en esta lavanderia.")
    return vehicle


def _resolve_invoice_client(session, lavanderia_id, ruc_ci, razon_social):
    """Busca o crea un cliente facturable por RUC/CI."""
    existing = get_client_by_ruc_ci(session, lavanderia_id, ruc_ci)
    if existing is not None:
        return existing

    customer_type = "empresa" if is_company_name(razon_social) else "particular"
    return create_client(
        session,
        lavanderia_id=lavanderia_id,
        nombre=razon_social,
        tipo_cliente=customer_type,
        ruc_ci=ruc_ci,
        estado=True,
    )


def _resolve_sale_client(session, lavanderia_id, *, vehicle=None, requires_invoice=False, ruc_ci=None, razon_social=None):
    """Determina el cliente de la venta manteniendo compatibilidad con la UI actual."""
    if requires_invoice:
        if ruc_ci is None or razon_social is None:
            raise ValueError("Faltan datos de facturacion para el ingreso.")
        return _resolve_invoice_client(session, lavanderia_id, ruc_ci, razon_social)

    if vehicle is not None and vehicle.cliente_id is not None:
        client = session.get(Cliente, vehicle.cliente_id)
        if client is not None and client.lavanderia_id == lavanderia_id:
            return client

    generic = get_generic_client(session, lavanderia_id)
    if generic is None:
        raise ValueError("No existe un cliente generico configurado para esta lavanderia.")
    return generic


def _build_item_payload(service_id, product_id, amount):
    """Arma el único detalle que representa al ingreso legacy."""
    normalized_amount = _to_decimal_amount(amount)
    return {
        "cantidad": 1,
        "precio_unitario": normalized_amount,
        "subtotal": normalized_amount,
        "servicio_id": service_id,
        "producto_id": product_id,
    }


def _serialize_income_row(sale, item, service=None, product=None, vehicle=None, vehicle_type=None, vehicle_client=None, sale_client=None, user=None):
    """Convierte venta + detalle en un registro compatible con la UI heredada."""
    item_name = service.nombre_servicio if service is not None else None
    if item_name is None and product is not None:
        item_name = product.nombre_producto

    requires_invoice = bool(sale.requiere_factura)

    return {
        "id": sale.id,
        "date": sale.fecha_venta,
        "service_id": item.servicio_id,
        "product_id": item.producto_id,
        "service": item_name,
        "vehicle_id": sale.vehiculo_id,
        "license_plate": vehicle.matricula if vehicle is not None else None,
        "vehicle_type_id": vehicle.tipo_vehiculo_id if vehicle is not None else None,
        "vehicle_type": vehicle_type.nombre if vehicle_type is not None else None,
        "owner_name": vehicle_client.nombre if vehicle_client is not None else None,
        "phone": vehicle_client.telefono if vehicle_client is not None else None,
        "amount": float(item.subtotal),
        "payment_method": sale.metodo_pago,
        "payment_type": sale.tipo_cobro,
        "requires_invoice": 1 if requires_invoice else 0,
        "ruc_ci": sale_client.ruc_ci if requires_invoice and sale_client is not None else None,
        "razon_social": sale_client.nombre if requires_invoice and sale_client is not None else None,
        "notes": sale.observacion,
        "created_by": user.nombre_usuario if user is not None else None,
        "created_at": sale.created_at,
    }


def _income_select(lavanderia_id):
    """Select base para listar ingresos legacy desde ventas + detalles."""
    vehicle_client = aliased(Cliente)
    sale_client = aliased(Cliente)

    return (
        select(
            Venta,
            DetalleVenta,
            Servicio,
            Producto,
            Vehiculo,
            TipoVehiculo,
            vehicle_client,
            Usuario,
            sale_client,
        )
        .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        .outerjoin(Servicio, Servicio.id == DetalleVenta.servicio_id)
        .outerjoin(Producto, Producto.id == DetalleVenta.producto_id)
        .outerjoin(Vehiculo, Vehiculo.id == Venta.vehiculo_id)
        .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
        .outerjoin(vehicle_client, vehicle_client.id == Vehiculo.cliente_id)
        .join(Usuario, Usuario.id == Venta.usuario_id)
        .join(sale_client, sale_client.id == Venta.cliente_id)
        .where(Venta.lavanderia_id == lavanderia_id)
    )


def create_income(
    date,
    service_id,
    amount,
    payment_method,
    notes,
    vehicle_id,
    created_at=None,
    payment_type="Contado",
    requires_invoice=0,
    ruc_ci=None,
    razon_social=None,
    created_by=None,
    product_id=None,
    *,
    lavanderia_id=None,
    user_id=None,
):
    """Inserta un nuevo ingreso sobre ventas + detalle_venta y devuelve el id de la venta."""
    del created_at
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    income_date = _parse_date_like(date)
    normalized_notes = _clean_optional_text(notes)
    normalized_payment_method = _clean_optional_text(payment_method)
    normalized_ruc_ci = _clean_optional_text(ruc_ci)
    normalized_razon_social = _clean_optional_text(razon_social)

    with SessionLocal() as session:
        user = _resolve_user(
            session,
            resolved_lavanderia_id,
            user_id=user_id,
            created_by=created_by,
        )
        vehicle = _resolve_vehicle(session, resolved_lavanderia_id, vehicle_id)
        client = _resolve_sale_client(
            session,
            resolved_lavanderia_id,
            vehicle=vehicle,
            requires_invoice=bool(requires_invoice),
            ruc_ci=normalized_ruc_ci,
            razon_social=normalized_razon_social,
        )

        sale = create_sale(
            session,
            fecha_venta=income_date,
            tipo_cobro=payment_type,
            total=_to_decimal_amount(amount),
            cliente_id=client.id,
            lavanderia_id=resolved_lavanderia_id,
            usuario_id=user.id,
            metodo_pago=normalized_payment_method,
            requiere_factura=bool(requires_invoice),
            observacion=normalized_notes,
            vehiculo_id=vehicle.id if vehicle is not None else None,
        )
        item = _build_item_payload(service_id, product_id, amount)
        create_sale_item(
            session,
            venta_id=sale.id,
            cantidad=item["cantidad"],
            precio_unitario=item["precio_unitario"],
            subtotal=item["subtotal"],
            servicio_id=item["servicio_id"],
            producto_id=item["producto_id"],
        )
        session.commit()
        return sale.id


def get_incomes(start_date=None, end_date=None, lavanderia_id=None):
    """Devuelve ingresos legacy del tenant actual, opcionalmente filtrados por fecha."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = _income_select(resolved_lavanderia_id)
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
        serialized_rows = []
        for sale, item, service, product, vehicle, vehicle_type, vehicle_client, user, sale_client in rows:
            serialized_rows.append(
                _serialize_income_row(
                    sale,
                    item,
                    service=service,
                    product=product,
                    vehicle=vehicle,
                    vehicle_type=vehicle_type,
                    vehicle_client=vehicle_client,
                    sale_client=sale_client,
                    user=user,
                )
            )
        return serialized_rows


def get_income_by_id(income_id, lavanderia_id=None):
    """Busca un ingreso legacy por id de venta y devuelve su primer detalle."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = _income_select(resolved_lavanderia_id).where(Venta.id == income_id)
        row = session.execute(
            query.order_by(DetalleVenta.id.asc())
        ).first()
        if row is None:
            return None

        sale, item, service, product, vehicle, vehicle_type, vehicle_client, user, sale_client = row
        return _serialize_income_row(
            sale,
            item,
            service=service,
            product=product,
            vehicle=vehicle,
            vehicle_type=vehicle_type,
            vehicle_client=vehicle_client,
            sale_client=sale_client,
            user=user,
        )


def update_income(
    income_id,
    date,
    service_id,
    amount,
    payment_method,
    notes,
    vehicle_id=None,
    payment_type="Contado",
    requires_invoice=0,
    ruc_ci=None,
    razon_social=None,
    product_id=None,
    *,
    lavanderia_id=None,
):
    """Actualiza una venta legacy reemplazando su único detalle."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    income_date = _parse_date_like(date)
    normalized_notes = _clean_optional_text(notes)
    normalized_payment_method = _clean_optional_text(payment_method)
    normalized_ruc_ci = _clean_optional_text(ruc_ci)
    normalized_razon_social = _clean_optional_text(razon_social)

    with SessionLocal() as session:
        sale = get_sale_by_id(session, resolved_lavanderia_id, income_id)
        if sale is None:
            raise ValueError("El ingreso indicado no existe.")

        vehicle = _resolve_vehicle(session, resolved_lavanderia_id, vehicle_id)
        client = _resolve_sale_client(
            session,
            resolved_lavanderia_id,
            vehicle=vehicle,
            requires_invoice=bool(requires_invoice),
            ruc_ci=normalized_ruc_ci,
            razon_social=normalized_razon_social,
        )

        update_sale(
            session,
            sale,
            fecha_venta=income_date,
            tipo_cobro=payment_type,
            total=_to_decimal_amount(amount),
            cliente_id=client.id,
            usuario_id=sale.usuario_id,
            metodo_pago=normalized_payment_method,
            requiere_factura=bool(requires_invoice),
            observacion=normalized_notes,
            vehiculo_id=vehicle.id if vehicle is not None else None,
        )
        delete_sale_items(session, sale.id)
        item = _build_item_payload(service_id, product_id, amount)
        create_sale_item(
            session,
            venta_id=sale.id,
            cantidad=item["cantidad"],
            precio_unitario=item["precio_unitario"],
            subtotal=item["subtotal"],
            servicio_id=item["servicio_id"],
            producto_id=item["producto_id"],
        )
        session.commit()


def update_income_payment_type(income_id, payment_type, lavanderia_id=None):
    """Actualiza solo el tipo de cobro de una venta legacy."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        sale = get_sale_by_id(session, resolved_lavanderia_id, income_id)
        if sale is None:
            raise ValueError("El ingreso indicado no existe.")
        sale.tipo_cobro = payment_type
        session.commit()


def delete_income(income_id, lavanderia_id=None):
    """Elimina un ingreso legacy por id de venta."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        sale = get_sale_by_id(session, resolved_lavanderia_id, income_id)
        if sale is None:
            raise ValueError("El ingreso indicado no existe.")
        delete_sale(session, sale)
        session.commit()


def get_last_income_by_vehicle(vehicle_id, lavanderia_id=None):
    """Devuelve el ultimo ingreso registrado para un vehiculo dado."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            _income_select(resolved_lavanderia_id)
            .where(Venta.vehiculo_id == vehicle_id)
            .order_by(Venta.id.desc(), DetalleVenta.id.asc())
        )
        row = session.execute(query).first()
        if row is None:
            return None

        sale, item, service, product, vehicle, vehicle_type, vehicle_client, user, sale_client = row
        return _serialize_income_row(
            sale,
            item,
            service=service,
            product=product,
            vehicle=vehicle,
            vehicle_type=vehicle_type,
            vehicle_client=vehicle_client,
            sale_client=sale_client,
            user=user,
        )


def get_product_stats(start_date, end_date, lavanderia_id=None):
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


def get_income_count_by_period(start_date, end_date, lavanderia_id=None):
    """Cuenta el numero de ingresos de servicios en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.count(DetalleVenta.id)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
            DetalleVenta.servicio_id.is_not(None),
        )
        return session.scalar(query) or 0


def get_product_count_by_period(start_date, end_date, lavanderia_id=None):
    """Cuenta el numero de ventas de productos en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.count(DetalleVenta.id)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
            DetalleVenta.producto_id.is_not(None),
        )
        return session.scalar(query) or 0


def get_income_total_by_period(start_date, end_date, lavanderia_id=None):
    """Calcula el total de ingresos en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.coalesce(func.sum(DetalleVenta.subtotal), 0)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
        )
        total = session.scalar(query)
        return float(total or 0)


def get_income_grouped_by_service(start_date, end_date, lavanderia_id=None):
    """Agrupa ingresos por servicio o producto para un periodo dado."""
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


def get_service_income_total(start_date, end_date, lavanderia_id=None):
    """Calcula el total de ingresos de servicios en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.coalesce(func.sum(DetalleVenta.subtotal), 0)).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).where(
            Venta.lavanderia_id == resolved_lavanderia_id,
            Venta.fecha_venta.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
            DetalleVenta.servicio_id.is_not(None),
        )
        total = session.scalar(query)
        return float(total or 0)


def get_income_total_by_payment_type(start_date, end_date, lavanderia_id=None):
    """Devuelve totales de ingresos separados por tipo de cobro."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(
                func.coalesce(Venta.tipo_cobro, "Contado").label("payment_type"),
                func.coalesce(func.sum(DetalleVenta.subtotal), 0).label("total"),
            )
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
            )
            .group_by(func.coalesce(Venta.tipo_cobro, "Contado"))
        )
        rows = session.execute(query).all()
        return {payment_type: float(total) for payment_type, total in rows}


def get_razon_social_by_ruc_ci(ruc_ci, lavanderia_id=None):
    """Devuelve el nombre del cliente ya registrado para un RUC/CI dado."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    normalized_ruc_ci = _clean_optional_text(ruc_ci)
    if normalized_ruc_ci is None:
        return None

    with SessionLocal() as session:
        client = get_client_by_ruc_ci(session, resolved_lavanderia_id, normalized_ruc_ci)
        return client.nombre if client is not None else None


def get_income_grouped_by_razon_social(start_date, end_date, income_type=None, lavanderia_id=None):
    """Devuelve totales de ingresos agrupados por razon social."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(
                Cliente.nombre.label("razon_social"),
                Cliente.ruc_ci.label("ruc_ci"),
                func.count(DetalleVenta.id).label("count"),
                func.coalesce(func.sum(DetalleVenta.subtotal), 0).label("total"),
            )
            .join(Venta, Venta.cliente_id == Cliente.id)
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
                Venta.requiere_factura.is_(True),
                Cliente.ruc_ci.is_not(None),
            )
        )

        if income_type == "service":
            query = query.where(DetalleVenta.servicio_id.is_not(None))
        elif income_type == "product":
            query = query.where(DetalleVenta.producto_id.is_not(None))

        query = query.group_by(Cliente.nombre, Cliente.ruc_ci).order_by(
            func.sum(DetalleVenta.subtotal).desc()
        )
        rows = session.execute(query).all()
        return [
            {
                "razon_social": razon_social,
                "ruc_ci": customer_ruc_ci,
                "count": count,
                "total": float(total),
            }
            for razon_social, customer_ruc_ci, count, total in rows
        ]


def get_income_detail_by_razon_social(start_date, end_date, razon_social, lavanderia_id=None):
    """Devuelve detalle de ingresos facturados para una empresa especifica."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        item_name = func.coalesce(Servicio.nombre_servicio, Producto.nombre_producto)
        query = (
            select(
                Venta.fecha_venta.label("date"),
                item_name.label("service"),
                TipoVehiculo.nombre.label("vehicle_type"),
                DetalleVenta.subtotal.label("amount"),
            )
            .join(Venta, Venta.cliente_id == Cliente.id)
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .outerjoin(Servicio, Servicio.id == DetalleVenta.servicio_id)
            .outerjoin(Producto, Producto.id == DetalleVenta.producto_id)
            .outerjoin(Vehiculo, Vehiculo.id == Venta.vehiculo_id)
            .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
            .where(
                Venta.lavanderia_id == resolved_lavanderia_id,
                Venta.fecha_venta.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
                Cliente.nombre == razon_social,
            )
            .order_by(Venta.fecha_venta.asc(), DetalleVenta.subtotal.desc())
        )
        rows = session.execute(query).all()
        return [
            {
                "date": row.date,
                "service": row.service,
                "vehicle_type": row.vehicle_type,
                "amount": float(row.amount),
            }
            for row in rows
        ]


def get_daily_incomes(start_date, end_date, lavanderia_id=None):
    """Devuelve ingresos totales agrupados por dia para el periodo dado."""
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


def get_customer_stats(start_date, end_date, lavanderia_id=None):
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
