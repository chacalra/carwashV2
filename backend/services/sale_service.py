"""Reglas de negocio para ventas de la V2."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import Cliente, Producto, Servicio, Usuario, Vehiculo
from backend.repositories.clients_repository import create_client, get_client_by_ruc_ci, get_generic_client
from backend.repositories.sale_items_repository import create_sale_items, delete_sale_items
from backend.repositories.sales_repository import create_sale, delete_sale, get_sale_by_id, update_sale, void_sale


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


def _normalize_required_invoice_text(value, field_name):
    """Valida datos obligatorios de facturación manual."""
    normalized = _normalize_optional_text(value)
    if normalized is None:
        raise ValueError(f"El campo {field_name} es obligatorio cuando se genera factura.")
    return normalized


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


def _resolve_sale_client(
    session,
    lavanderia_id,
    client_id,
    requiere_factura,
    vehicle=None,
    ruc_ci=None,
    razon_social=None,
):
    """Resuelve el cliente comercial de la venta según el flujo operativo."""
    if requiere_factura:
        normalized_ruc_ci = _normalize_required_invoice_text(ruc_ci, "RUC/CI")
        normalized_razon_social = _normalize_required_invoice_text(
            razon_social,
            "Razon Social",
        )

        existing_client = get_client_by_ruc_ci(
            session,
            lavanderia_id,
            normalized_ruc_ci,
        )
        if existing_client is not None:
            if not existing_client.estado:
                raise ValueError(
                    "Ya existe un cliente inactivo con ese RUC/CI en esta lavanderia."
                )
            client = existing_client
        else:
            client = create_client(
                session,
                lavanderia_id=lavanderia_id,
                nombre=normalized_razon_social,
                tipo_cliente="empresa",
                ruc_ci=normalized_ruc_ci,
                telefono=None,
                email=None,
                estado=True,
            )

        if vehicle is not None and vehicle.cliente_id is not None and vehicle.cliente_id != client.id:
            raise ValueError(
                "El vehiculo seleccionado pertenece a otro cliente dentro de la lavanderia."
            )
        return client

    if client_id is not None:
        client = _get_active_client(
            session,
            lavanderia_id,
            client_id,
            requiere_factura=False,
        )
        if vehicle is not None and vehicle.cliente_id is not None and vehicle.cliente_id != client.id:
            raise ValueError(
                "El vehiculo seleccionado pertenece a otro cliente dentro de la lavanderia."
            )
        return client

    if vehicle is not None and vehicle.cliente_id is not None:
        client = session.get(Cliente, vehicle.cliente_id)
        if client is None or client.lavanderia_id != lavanderia_id:
            raise ValueError("El cliente del vehiculo no existe en esta lavanderia.")
        if not client.estado:
            raise ValueError("No se puede registrar una venta con un cliente inactivo.")
        return client

    generic_client = get_generic_client(session, lavanderia_id)
    if generic_client is None or not generic_client.estado:
        raise ValueError(
            "No existe un cliente generico activo configurado para esta lavanderia."
        )
    return generic_client


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


def _get_valid_vehicle(session, lavanderia_id, vehiculo_id):
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
        if quantity != 1:
            raise ValueError("El servicio principal debe registrarse una sola vez por venta.")

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
    cliente_id=None,
    fecha_venta,
    tipo_cobro,
    items,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
    ruc_ci=None,
    razon_social=None,
):
    """Valida y normaliza una venta antes de persistirla."""
    normalized_date = _normalize_sale_date(fecha_venta)
    normalized_tipo_cobro = _normalize_tipo_cobro(tipo_cobro)
    normalized_metodo_pago = _normalize_optional_text(metodo_pago)
    normalized_observacion = _normalize_optional_text(observacion)

    if not isinstance(items, list) or not items:
        raise ValueError("La venta debe tener al menos un detalle.")

    vehicle = _get_valid_vehicle(session, lavanderia_id, vehiculo_id)
    client = _resolve_sale_client(
        session,
        lavanderia_id,
        cliente_id,
        requiere_factura,
        vehicle=vehicle,
        ruc_ci=ruc_ci,
        razon_social=razon_social,
    )
    _get_active_user(session, lavanderia_id, usuario_id)

    normalized_items = [
        _build_sale_item(session, lavanderia_id, raw_item)
        for raw_item in items
    ]

    service_count = sum(1 for item in normalized_items if item["servicio_id"] is not None)
    if service_count > 1:
        raise ValueError("La venta puede tener como maximo un servicio principal.")

    # Regla: el vehiculo se asocia a servicios. Con servicio el vehiculo es
    # obligatorio; sin servicio no debe ingresarse.
    if service_count > 0 and vehiculo_id is None:
        raise ValueError("Se requiere un vehiculo cuando la venta incluye servicios.")
    if service_count == 0 and vehiculo_id is not None:
        raise ValueError("El vehiculo no aplica para ventas de solo productos.")

    product_ids = [
        item["producto_id"]
        for item in normalized_items
        if item["producto_id"] is not None
    ]
    if len(product_ids) != len(set(product_ids)):
        raise ValueError("Cada producto debe cargarse en una sola linea de la venta.")

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
    fecha_venta,
    tipo_cobro,
    items,
    cliente_id=None,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
    ruc_ci=None,
    razon_social=None,
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
            ruc_ci=ruc_ci,
            razon_social=razon_social,
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
    fecha_venta,
    tipo_cobro,
    items,
    cliente_id=None,
    metodo_pago=None,
    requiere_factura=False,
    observacion=None,
    vehiculo_id=None,
    ruc_ci=None,
    razon_social=None,
):
    """Valida y actualiza una venta existente junto con sus detalles."""
    with SessionLocal() as session:
        sale = get_sale_by_id(session, lavanderia_id, sale_id)
        if sale is None:
            raise ValueError("La venta indicada no existe en esta lavanderia.")
        if not sale.estado:
            raise ValueError("No se puede editar una venta que ya fue anulada.")

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
            ruc_ci=ruc_ci,
            razon_social=razon_social,
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
        return sale.id


def remove_sale(lavanderia_id, sale_id):
    """Anula una venta de forma logica."""
    with SessionLocal() as session:
        sale = get_sale_by_id(session, lavanderia_id, sale_id)
        if sale is None:
            raise ValueError("La venta indicada no existe en esta lavanderia.")
        if not sale.estado:
            raise ValueError("La venta ya fue anulada.")

        void_sale(session, sale)
        session.commit()


def update_sale_payment_type(lavanderia_id, sale_id, tipo_cobro):
    """Actualiza solo el tipo de cobro de una venta existente."""
    normalized_tipo_cobro = _normalize_tipo_cobro(tipo_cobro)

    with SessionLocal() as session:
        sale = get_sale_by_id(session, lavanderia_id, sale_id)
        if sale is None:
            raise ValueError("La venta indicada no existe en esta lavanderia.")
        if not sale.estado:
            raise ValueError("No se puede editar una venta que ya fue anulada.")

        sale.tipo_cobro = normalized_tipo_cobro
        session.commit()
