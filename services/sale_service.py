"""Reglas de negocio para ventas de la V2."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import Cliente, Producto, Servicio, Usuario, Vehiculo
from repositories.sale_items_repository import create_sale_items, delete_sale_items
from repositories.sales_repository import create_sale, delete_sale, get_sale_by_id, update_sale


VALID_TIPO_COBRO = ("Contado", "Credito")
MONEY_QUANTIZER = Decimal("0.01")


def _normalize_sale_date(fecha_venta):
    """Normaliza una fecha operativa recibida como date o ISO string."""
    if isinstance(fecha_venta, date):
        return fecha_venta

    if isinstance(fecha_venta, str) and fecha_venta.strip():
        try:
            return date.fromisoformat(fecha_venta.strip())
        except ValueError as exc:
            raise ValueError("La fecha de la venta debe tener formato YYYY-MM-DD.") from exc

    raise ValueError("La fecha de la venta es obligatoria.")


def _normalize_optional_text(value):
    """Normaliza textos opcionales."""
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    return normalized or None


def _normalize_tipo_cobro(tipo_cobro):
    """Valida el tipo de cobro permitido."""
    normalized = tipo_cobro.strip() if isinstance(tipo_cobro, str) else ""
    if normalized not in VALID_TIPO_COBRO:
        raise ValueError("El tipo de cobro debe ser Contado o Credito.")
    return normalized


def _normalize_quantity(value):
    """Valida que la cantidad sea un entero positivo."""
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("La cantidad de cada detalle debe ser un entero positivo.") from exc

    if quantity <= 0:
        raise ValueError("La cantidad de cada detalle debe ser mayor que cero.")

    return quantity


def _normalize_money(value, field_name):
    """Normaliza importes monetarios a Decimal con dos decimales."""
    try:
        normalized = Decimal(str(value)).quantize(
            MONEY_QUANTIZER,
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"El campo {field_name} debe ser un monto valido.") from exc

    if normalized < 0:
        raise ValueError(f"El campo {field_name} no puede ser negativo.")

    return normalized


def _get_active_client(session, lavanderia_id, client_id, requiere_factura):
    """Busca y valida el cliente asociado a la venta."""
    client = session.scalar(
        select(Cliente).where(
            Cliente.id == client_id,
            Cliente.lavanderia_id == lavanderia_id,
        )
    )
    if client is None:
        raise ValueError("El cliente indicado no existe en esta lavanderia.")

    if not client.estado:
        raise ValueError("No se puede registrar una venta con un cliente inactivo.")

    if requiere_factura and (client.tipo_cliente == "generico" or not client.ruc_ci):
        raise ValueError(
            "Para facturar se necesita un cliente identificable con RUC/CI."
        )

    return client


def _get_active_user(session, lavanderia_id, usuario_id):
    """Busca y valida el usuario que registra la venta."""
    user = session.scalar(
        select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.lavanderia_id == lavanderia_id,
        )
    )
    if user is None:
        raise ValueError("El usuario indicado no existe en esta lavanderia.")

    if not user.estado:
        raise ValueError("No se puede registrar una venta con un usuario inactivo.")

    return user


def _get_valid_vehicle(session, lavanderia_id, vehiculo_id, client_id):
    """Valida el vehiculo opcional asociado a la venta."""
    if vehiculo_id is None:
        return None

    vehicle = session.scalar(
        select(Vehiculo).where(
            Vehiculo.id == vehiculo_id,
            Vehiculo.lavanderia_id == lavanderia_id,
        )
    )
    if vehicle is None:
        raise ValueError("El vehiculo indicado no existe en esta lavanderia.")

    if not vehicle.estado:
        raise ValueError("No se puede registrar una venta con un vehiculo inactivo.")

    if vehicle.cliente_id is not None and vehicle.cliente_id != client_id:
        raise ValueError(
            "El vehiculo seleccionado pertenece a otro cliente dentro de la lavanderia."
        )

    return vehicle


def _build_sale_item(session, lavanderia_id, raw_item):
    """Valida un detalle de venta y devuelve su estructura persistible."""
    service_id = raw_item.get("servicio_id")
    product_id = raw_item.get("producto_id")

    if (service_id is None and product_id is None) or (
        service_id is not None and product_id is not None
    ):
        raise ValueError(
            "Cada detalle debe tener exactamente un servicio o un producto."
        )

    quantity = _normalize_quantity(raw_item.get("cantidad", 1))

    if service_id is not None:
        service = session.scalar(
            select(Servicio).where(
                Servicio.id == service_id,
                Servicio.lavanderia_id == lavanderia_id,
            )
        )
        if service is None:
            raise ValueError("El servicio indicado no existe en esta lavanderia.")
        if not service.estado:
            raise ValueError("No se puede vender un servicio inactivo.")

        default_price = service.precio
        normalized_price = _normalize_money(
            raw_item.get("precio_unitario", default_price),
            "precio_unitario",
        )
        subtotal = (normalized_price * quantity).quantize(
            MONEY_QUANTIZER,
            rounding=ROUND_HALF_UP,
        )
        return {
            "cantidad": quantity,
            "precio_unitario": normalized_price,
            "subtotal": subtotal,
            "servicio_id": service_id,
            "producto_id": None,
        }

    product = session.scalar(
        select(Producto).where(
            Producto.id == product_id,
            Producto.lavanderia_id == lavanderia_id,
        )
    )
    if product is None:
        raise ValueError("El producto indicado no existe en esta lavanderia.")
    if not product.estado:
        raise ValueError("No se puede vender un producto inactivo.")

    default_price = product.precio
    normalized_price = _normalize_money(
        raw_item.get("precio_unitario", default_price),
        "precio_unitario",
    )
    subtotal = (normalized_price * quantity).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )
    return {
        "cantidad": quantity,
        "precio_unitario": normalized_price,
        "subtotal": subtotal,
        "servicio_id": None,
        "producto_id": product_id,
    }


def validate_sale_data(
    session,
    *,
    lavanderia_id,
    usuario_id,
    cliente_id,
    fecha_venta,
    tipo_cobro,
    items,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
):
    """Valida y normaliza una venta antes de persistirla."""
    normalized_date = _normalize_sale_date(fecha_venta)
    normalized_tipo_cobro = _normalize_tipo_cobro(tipo_cobro)
    normalized_metodo_pago = _normalize_optional_text(metodo_pago)
    normalized_observacion = _normalize_optional_text(observacion)

    if not isinstance(items, list) or not items:
        raise ValueError("La venta debe tener al menos un detalle.")

    client = _get_active_client(
        session,
        lavanderia_id,
        cliente_id,
        requiere_factura,
    )
    _get_active_user(session, lavanderia_id, usuario_id)
    _get_valid_vehicle(session, lavanderia_id, vehiculo_id, client.id)

    normalized_items = [
        _build_sale_item(session, lavanderia_id, raw_item)
        for raw_item in items
    ]
    total = sum(
        (item["subtotal"] for item in normalized_items),
        start=Decimal("0.00"),
    ).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    return {
        "fecha_venta": normalized_date,
        "tipo_cobro": normalized_tipo_cobro,
        "metodo_pago": normalized_metodo_pago,
        "requiere_factura": bool(requiere_factura),
        "observacion": normalized_observacion,
        "cliente_id": client.id,
        "usuario_id": usuario_id,
        "vehiculo_id": vehiculo_id,
        "items": normalized_items,
        "total": total,
    }


def register_sale(
    lavanderia_id,
    usuario_id,
    cliente_id,
    fecha_venta,
    tipo_cobro,
    items,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
):
    """Valida y registra una venta con uno o varios detalles."""
    with SessionLocal() as session:
        validated_data = validate_sale_data(
            session,
            lavanderia_id=lavanderia_id,
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            fecha_venta=fecha_venta,
            tipo_cobro=tipo_cobro,
            items=items,
            metodo_pago=metodo_pago,
            requiere_factura=requiere_factura,
            observacion=observacion,
            vehiculo_id=vehiculo_id,
        )

        sale = create_sale(
            session,
            fecha_venta=validated_data["fecha_venta"],
            tipo_cobro=validated_data["tipo_cobro"],
            total=validated_data["total"],
            cliente_id=validated_data["cliente_id"],
            lavanderia_id=lavanderia_id,
            usuario_id=validated_data["usuario_id"],
            metodo_pago=validated_data["metodo_pago"],
            requiere_factura=validated_data["requiere_factura"],
            observacion=validated_data["observacion"],
            vehiculo_id=validated_data["vehiculo_id"],
        )
        create_sale_items(session, sale.id, validated_data["items"])
        session.commit()
        return sale.id


def edit_sale(
    lavanderia_id,
    sale_id,
    usuario_id,
    cliente_id,
    fecha_venta,
    tipo_cobro,
    items,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
):
    """Valida y actualiza una venta existente junto con sus detalles."""
    with SessionLocal() as session:
        sale = get_sale_by_id(session, lavanderia_id, sale_id)
        if sale is None:
            raise ValueError("La venta indicada no existe en esta lavanderia.")

        validated_data = validate_sale_data(
            session,
            lavanderia_id=lavanderia_id,
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            fecha_venta=fecha_venta,
            tipo_cobro=tipo_cobro,
            items=items,
            metodo_pago=metodo_pago,
            requiere_factura=requiere_factura,
            observacion=observacion,
            vehiculo_id=vehiculo_id,
        )

        update_sale(
            session,
            sale,
            fecha_venta=validated_data["fecha_venta"],
            tipo_cobro=validated_data["tipo_cobro"],
            total=validated_data["total"],
            cliente_id=validated_data["cliente_id"],
            usuario_id=validated_data["usuario_id"],
            metodo_pago=validated_data["metodo_pago"],
            requiere_factura=validated_data["requiere_factura"],
            observacion=validated_data["observacion"],
            vehiculo_id=validated_data["vehiculo_id"],
        )
        delete_sale_items(session, sale.id)
        create_sale_items(session, sale.id, validated_data["items"])
        session.commit()


def remove_sale(lavanderia_id, sale_id):
    """Elimina una venta existente."""
    with SessionLocal() as session:
        sale = get_sale_by_id(session, lavanderia_id, sale_id)
        if sale is None:
            raise ValueError("La venta indicada no existe en esta lavanderia.")

        delete_sale(session, sale)
        session.commit()
