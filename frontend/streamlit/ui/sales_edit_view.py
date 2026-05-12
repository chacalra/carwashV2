"""Vista inicial para editar ventas nativas de la V2."""

from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import streamlit as st
from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import Cliente, Producto, Servicio, TipoVehiculo, Vehiculo
from backend.repositories.sale_items_repository import list_sale_items
from backend.repositories.sales_repository import get_sale_by_id, list_sales
from backend.services.sale_service import edit_sale
from frontend.streamlit.utils.formatters import format_currency
from frontend.streamlit.utils.notifications import notify

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Tarjeta", "QR"]


def _load_active_clients(lavanderia_id):
    with SessionLocal() as session:
        query = (
            select(Cliente)
            .where(
                Cliente.lavanderia_id == lavanderia_id,
                Cliente.estado.is_(True),
            )
            .order_by(Cliente.nombre.asc(), Cliente.id.asc())
        )
        clients = session.scalars(query).all()
        return [
            {
                "id": client.id,
                "name": client.nombre,
                "type": client.tipo_cliente,
                "ruc_ci": client.ruc_ci,
            }
            for client in clients
        ]


def _load_client_vehicles(lavanderia_id, client_id):
    with SessionLocal() as session:
        query = (
            select(Vehiculo, TipoVehiculo)
            .join(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
            .where(
                Vehiculo.lavanderia_id == lavanderia_id,
                Vehiculo.cliente_id == client_id,
                Vehiculo.estado.is_(True),
            )
            .order_by(Vehiculo.matricula.asc().nulls_last(), Vehiculo.id.asc())
        )
        rows = session.execute(query).all()
        return [
            {
                "id": vehicle.id,
                "label": f"{vehicle.matricula or 'Sin matricula'} — {vehicle_type.nombre}",
            }
            for vehicle, vehicle_type in rows
        ]


def _build_client_options(clients):
    options = {}
    for client in clients:
        label = client["name"]
        if client["type"] == "generico":
            label = f"{label} (generico)"
        elif client["ruc_ci"]:
            label = f"{label} — {client['ruc_ci']}"
        options[label] = client
    return options


def _sale_label(sale):
    client_name = sale["client_name"]
    vehicle_label = sale["vehicle_label"] or "Sin vehiculo"
    return (
        f"{sale['date']} | #{sale['id']} | {client_name} | "
        f"{vehicle_label} | {format_currency(sale['total'])}"
    )


def _load_recent_sales(lavanderia_id):
    today = date.today()
    yesterday = today - timedelta(days=1)

    with SessionLocal() as session:
        sales = list_sales(
            session,
            lavanderia_id,
            start_date=yesterday,
            end_date=today,
        )
        rows = []
        for sale in sales:
            client = session.get(Cliente, sale.cliente_id)
            vehicle = session.get(Vehiculo, sale.vehiculo_id) if sale.vehiculo_id else None
            rows.append(
                {
                    "id": sale.id,
                    "date": sale.fecha_venta,
                    "client_name": client.nombre if client is not None else "Cliente desconocido",
                    "vehicle_label": vehicle.matricula if vehicle is not None else None,
                    "total": Decimal(str(sale.total)),
                }
            )
        return rows


def _load_sale_detail(lavanderia_id, sale_id):
    with SessionLocal() as session:
        sale = get_sale_by_id(session, lavanderia_id, sale_id)
        if sale is None:
            return None

        client = session.get(Cliente, sale.cliente_id)
        vehicle = session.get(Vehiculo, sale.vehiculo_id) if sale.vehiculo_id else None
        items = []

        for item in list_sale_items(session, sale.id):
            service = session.get(Servicio, item.servicio_id) if item.servicio_id else None
            product = session.get(Producto, item.producto_id) if item.producto_id else None
            if service is not None:
                items.append(
                    {
                        "type": "Servicio",
                        "concept_id": service.id,
                        "concept_name": service.nombre_servicio,
                        "quantity": item.cantidad,
                        "unit_price": Decimal(str(item.precio_unitario)),
                    }
                )
            elif product is not None:
                items.append(
                    {
                        "type": "Producto",
                        "concept_id": product.id,
                        "concept_name": product.nombre_producto,
                        "quantity": item.cantidad,
                        "unit_price": Decimal(str(item.precio_unitario)),
                    }
                )

        return {
            "id": sale.id,
            "fecha_venta": sale.fecha_venta,
            "tipo_cobro": sale.tipo_cobro,
            "metodo_pago": sale.metodo_pago,
            "requiere_factura": bool(sale.requiere_factura),
            "ruc_ci": client.ruc_ci if sale.requiere_factura and client is not None else "",
            "razon_social": client.nombre if sale.requiere_factura and client is not None else "",
            "observacion": sale.observacion or "",
            "cliente_id": sale.cliente_id,
            "vehiculo_id": sale.vehiculo_id,
            "items": items,
            "client_name": client.nombre if client is not None else "Cliente desconocido",
            "total": Decimal(str(sale.total)),
            "vehicle_label": vehicle.matricula if vehicle is not None else None,
        }


def _build_sale_item_payload(item_type, concept_id, quantity, unit_price):
    """Arma el payload de detalle esperado por sale_service."""
    item_key = "servicio_id" if item_type == "Servicio" else "producto_id"
    return {
        "cantidad": int(quantity),
        "precio_unitario": float(unit_price),
        item_key: concept_id,
    }


def _build_existing_sale_items_payload(items):
    """Conserva las lineas originales de una venta para guardarlas sin cambios."""
    return [
        _build_sale_item_payload(
            item["type"],
            item["concept_id"],
            item["quantity"],
            item["unit_price"],
        )
        for item in items
    ]


def _build_detail_dataframe(items):
    """Construye una tabla compacta de detalles de venta."""
    rows = []
    for item in items:
        unit_price = Decimal(str(item["unit_price"]))
        quantity = int(item["quantity"])
        subtotal = unit_price * quantity
        rows.append(
            {
                "Tipo": item["type"],
                "Concepto": item["concept_name"],
                "Cantidad": quantity,
                "Precio unitario": format_currency(unit_price),
                "Subtotal": format_currency(subtotal),
            }
        )
    return pd.DataFrame(rows)


def _calculate_items_total(items):
    """Calcula el total de las lineas existentes."""
    total = Decimal("0.00")
    for item in items:
        total += Decimal(str(item["unit_price"])) * int(item["quantity"])
    return total


def _invoice_key(sale_id):
    """Key estable para el checkbox de factura por venta."""
    return f"sales_edit_requires_invoice_{sale_id}"


def _ensure_invoice_state(state, sale_id, default_value):
    """Inicializa el estado de factura sin pisar cambios del usuario."""
    key = _invoice_key(sale_id)
    state.setdefault(key, bool(default_value))
    return key


def render_sales_edit_view():
    """Renderiza una primera UI nativa para editar ventas recientes."""
    st.title("Editar venta")
    st.caption("Solo se pueden editar ventas registradas hoy o ayer en esta primera version.")

    lavanderia_id = st.session_state.get("lavanderia_id")
    user_id = st.session_state.get("user_id")

    if lavanderia_id is None or user_id is None:
        st.error("Hace falta una lavanderia y un usuario activos para editar ventas.")
        return

    recent_sales = _load_recent_sales(lavanderia_id)
    if not recent_sales:
        st.info("No hay ventas de hoy ni de ayer para editar.")
        return

    sale_options = {_sale_label(sale): sale["id"] for sale in recent_sales}
    selected_sale_label = st.selectbox(
        "Seleccionar venta",
        options=list(sale_options.keys()),
        key="sales_edit_select",
    )
    sale_id = sale_options[selected_sale_label]
    sale = _load_sale_detail(lavanderia_id, sale_id)

    if sale is None:
        st.error("No se pudo cargar la venta seleccionada.")
        return

    clients = _load_active_clients(lavanderia_id)
    if not clients:
        st.warning("No hay clientes activos disponibles para editar esta venta.")
        return

    if not sale["items"]:
        st.warning("La venta seleccionada no tiene detalles para conservar.")
        return

    client_options = _build_client_options(clients)
    client_labels = list(client_options.keys())
    default_client_label = client_labels[0]
    for label, client in client_options.items():
        if client["id"] == sale["cliente_id"]:
            default_client_label = label
            break

    selected_client_label = st.selectbox(
        "Cliente *",
        options=client_labels,
        index=client_labels.index(default_client_label),
        key=f"sales_edit_client_select_{sale_id}",
    )
    selected_client = client_options[selected_client_label]

    vehicles = _load_client_vehicles(lavanderia_id, selected_client["id"])
    include_vehicle = bool(vehicles) and st.checkbox(
        "Asociar vehiculo existente",
        key=f"sales_edit_include_vehicle_{sale_id}",
        value=sale["vehiculo_id"] is not None,
    )
    selected_vehicle_id = None
    if include_vehicle:
        vehicle_options = {"Sin vehiculo": None}
        vehicle_options.update({vehicle["label"]: vehicle["id"] for vehicle in vehicles})
        vehicle_labels = list(vehicle_options.keys())
        default_vehicle_label = "Sin vehiculo"
        for label, vehicle_id in vehicle_options.items():
            if vehicle_id == sale["vehiculo_id"]:
                default_vehicle_label = label
                break
        selected_vehicle_label = st.selectbox(
            "Vehiculo",
            options=vehicle_labels,
            index=vehicle_labels.index(default_vehicle_label),
            key=f"sales_edit_vehicle_select_{sale_id}",
        )
        selected_vehicle_id = vehicle_options[selected_vehicle_label]

    sale_items = _build_existing_sale_items_payload(sale["items"])
    current_total = _calculate_items_total(sale["items"])
    invoice_key = _ensure_invoice_state(
        st.session_state,
        sale_id,
        sale["requiere_factura"],
    )

    st.checkbox("Generar factura", key=invoice_key)

    with st.form(f"sales_edit_form_{sale_id}"):
        sale_date = st.date_input("Fecha *", value=sale["fecha_venta"])
        payment_type = st.radio(
            "Tipo de cobro *",
            ["Contado", "Credito"],
            horizontal=True,
            index=1 if sale["tipo_cobro"] == "Credito" else 0,
        )

        default_payment_method = sale["metodo_pago"] if sale["metodo_pago"] in PAYMENT_METHODS else PAYMENT_METHODS[0]
        payment_method = st.selectbox(
            "Metodo de pago",
            PAYMENT_METHODS,
            index=PAYMENT_METHODS.index(default_payment_method),
        )
        requires_invoice = bool(st.session_state.get(invoice_key))
        if requires_invoice:
            invoice_ruc_ci = st.text_input(
                "RUC/CI *",
                value=sale["ruc_ci"],
                placeholder="Ej: 80012345-6 o 4567890",
            )
            invoice_razon_social = st.text_input(
                "Razon Social *",
                value=sale["razon_social"],
                placeholder="Ej: Empresa SA o Juan Perez",
            )
        else:
            invoice_ruc_ci = None
            invoice_razon_social = None

        observation = st.text_area(
            "Observacion (opcional)",
            value=sale["observacion"],
            placeholder="Ej: ajuste de productos o cambio de forma de cobro",
        )

        st.divider()
        st.subheader("Detalle")
        st.dataframe(
            _build_detail_dataframe(sale["items"]),
            width="stretch",
            hide_index=True,
        )
        st.info(f"Total: {format_currency(current_total)}")
        submitted = st.form_submit_button("Guardar cambios", type="primary")

    if not submitted:
        return

    try:
        edit_sale(
            lavanderia_id=lavanderia_id,
            sale_id=sale_id,
            usuario_id=user_id,
            cliente_id=selected_client["id"],
            fecha_venta=str(sale_date),
            tipo_cobro=payment_type,
            items=sale_items,
            metodo_pago=payment_method,
            requiere_factura=requires_invoice,
            observacion=observation,
            vehiculo_id=selected_vehicle_id,
            ruc_ci=invoice_ruc_ci,
            razon_social=invoice_razon_social,
        )
        notify(
            f"Venta actualizada #{sale_id} — {selected_client['name']} — "
            f"{format_currency(current_total)}"
        )
        st.rerun()
    except ValueError as error:
        st.error(str(error))
