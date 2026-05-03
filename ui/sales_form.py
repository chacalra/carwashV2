"""Vista inicial para registrar ventas nativas de la V2."""

from datetime import date
from decimal import Decimal

import streamlit as st
from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import Cliente, TipoVehiculo, Vehiculo
from repositories.products_repository import get_active_products
from repositories.services_repository import get_active_services
from services.sale_service import register_sale
from utils.formatters import format_currency
from utils.notifications import notify

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Tarjeta", "QR"]
ITEM_TYPES = ("Servicio", "Producto")


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


def render_sales_form():
    """Renderiza una primera UI nativa de ventas multi-item."""
    st.title("Registrar venta")
    st.caption("Formulario nativo V2 sobre `venta + detalle_venta`.")

    lavanderia_id = st.session_state.get("lavanderia_id")
    user_id = st.session_state.get("user_id")

    if lavanderia_id is None or user_id is None:
        st.error("Hace falta una lavanderia y un usuario activos para registrar ventas.")
        return

    clients = _load_active_clients(lavanderia_id)
    if not clients:
        st.warning("No hay clientes activos disponibles para registrar una venta.")
        return

    services = get_active_services(lavanderia_id=lavanderia_id)
    products = get_active_products(lavanderia_id=lavanderia_id)

    if not services and not products:
        st.warning("No hay servicios ni productos activos para vender.")
        return

    client_options = _build_client_options(clients)
    selected_client_label = st.selectbox(
        "Cliente *",
        options=list(client_options.keys()),
        key="sales_client_select",
    )
    selected_client = client_options[selected_client_label]

    vehicles = _load_client_vehicles(lavanderia_id, selected_client["id"])
    include_vehicle = bool(vehicles) and st.checkbox(
        "Asociar vehiculo existente",
        key="sales_include_vehicle",
    )
    selected_vehicle_id = None
    if include_vehicle:
        vehicle_options = {"Sin vehiculo": None}
        vehicle_options.update({vehicle["label"]: vehicle["id"] for vehicle in vehicles})
        selected_vehicle_label = st.selectbox(
            "Vehiculo",
            options=list(vehicle_options.keys()),
            key="sales_vehicle_select",
        )
        selected_vehicle_id = vehicle_options[selected_vehicle_label]

    line_count = st.number_input(
        "Cantidad de lineas",
        min_value=1,
        max_value=8,
        value=1,
        step=1,
        key="sales_line_count",
    )

    sale_items = []
    current_total = Decimal("0.00")

    with st.form("sales_form_v2", clear_on_submit=True):
        sale_date = st.date_input("Fecha *", value=date.today())
        payment_type = st.radio(
            "Tipo de cobro *",
            ["Contado", "Credito"],
            horizontal=True,
        )
        payment_method = st.selectbox("Metodo de pago", PAYMENT_METHODS)
        requires_invoice = st.checkbox("Generar factura")
        observation = st.text_area(
            "Observacion (opcional)",
            placeholder="Ej: venta mixta de lavado y productos",
        )

        st.divider()
        st.subheader("Detalle")

        for index in range(int(line_count)):
            st.markdown(f"**Linea {index + 1}**")
            item_type = st.selectbox(
                "Tipo",
                options=ITEM_TYPES,
                key=f"sales_item_type_{index}",
            )

            if item_type == "Servicio":
                if not services:
                    st.warning("No hay servicios activos para agregar en esta venta.")
                    return
                catalog = services
                item_key = "servicio_id"
            else:
                if not products:
                    st.warning("No hay productos activos para agregar en esta venta.")
                    return
                catalog = products
                item_key = "producto_id"

            item_options = {item["name"]: item for item in catalog}
            selected_item_name = st.selectbox(
                "Concepto",
                options=list(item_options.keys()),
                key=f"sales_item_name_{index}",
            )
            quantity = st.number_input(
                "Cantidad",
                min_value=1,
                step=1,
                value=1,
                key=f"sales_item_qty_{index}",
            )

            selected_item = item_options[selected_item_name]
            unit_price = Decimal(str(selected_item["price"]))
            subtotal = unit_price * quantity
            current_total += subtotal

            st.caption(
                f"Precio base: {format_currency(unit_price)} | "
                f"Subtotal: {format_currency(subtotal)}"
            )

            sale_payload = {
                "cantidad": int(quantity),
                item_key: selected_item["id"],
            }
            sale_items.append(sale_payload)
            st.divider()

        st.info(f"Total estimado: {format_currency(current_total)}")

        submitted = st.form_submit_button("Guardar venta", type="primary")

    if not submitted:
        return

    try:
        sale_id = register_sale(
            lavanderia_id=lavanderia_id,
            usuario_id=user_id,
            cliente_id=selected_client["id"],
            fecha_venta=str(sale_date),
            tipo_cobro=payment_type,
            items=sale_items,
            metodo_pago=payment_method,
            requiere_factura=requires_invoice,
            observacion=observation,
            vehiculo_id=selected_vehicle_id,
        )
        notify(
            f"Venta registrada #{sale_id} — {selected_client['name']} — "
            f"{format_currency(current_total)}"
        )
        for key in [
            "sales_client_select",
            "sales_include_vehicle",
            "sales_vehicle_select",
            "sales_line_count",
        ]:
            st.session_state.pop(key, None)
        st.rerun()
    except ValueError as error:
        st.error(str(error))
