"""Vista inicial para registrar ventas nativas de la V2."""

from datetime import date
from decimal import Decimal

import streamlit as st
from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.database.schema import Cliente
from backend.repositories.products_repository import get_active_products
from backend.repositories.services_repository import get_active_services
from backend.repositories.vehicle_types_repository import get_active_vehicle_types
from backend.services.sale_service import register_sale
from backend.services.vehicle_service import find_or_create_vehicle, normalize_plate
from frontend.streamlit.utils.formatters import format_currency
from frontend.streamlit.utils.notifications import notify

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Tarjeta", "QR"]
ITEM_TYPES = ("Servicio", "Producto")
LINE_COUNT_KEY = "sales_line_count"
MAX_LINES = 8


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


def _split_clients_for_sale(clients):
    """Separa cliente generico y clientes facturables para la UI de ventas."""
    generic_client = None
    billable_clients = []

    for client in clients:
        if client["type"] == "generico" and generic_client is None:
            generic_client = client
            continue

        if client["ruc_ci"]:
            billable_clients.append(client)

    return generic_client, billable_clients


def _find_client_by_ruc_ci(clients, ruc_ci):
    """Busca un cliente cargado en memoria por RUC/CI."""
    normalized_ruc_ci = ruc_ci.strip() if isinstance(ruc_ci, str) else ""
    if not normalized_ruc_ci:
        return None

    for client in clients:
        if client["ruc_ci"] == normalized_ruc_ci:
            return client
    return None


def _clean_optional_text(value):
    """Normaliza texto opcional para payloads de UI."""
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _build_vehicle_payload(license_plate, vehicle_type_id, owner_name=None, phone=None):
    """Devuelve los datos de vehiculo a resolver antes de guardar la venta."""
    normalized_plate = _clean_optional_text(license_plate)
    if normalized_plate is None:
        return None

    if vehicle_type_id is None:
        raise ValueError("El tipo de vehiculo es obligatorio cuando se indica matricula.")

    return {
        "license_plate": normalized_plate,
        "vehicle_type_id": vehicle_type_id,
        "owner_name": _clean_optional_text(owner_name),
        "phone": _clean_optional_text(phone),
    }


def _get_line_count():
    """Obtiene la cantidad actual de lineas del formulario."""
    return int(st.session_state.get(LINE_COUNT_KEY, 1))


def _get_available_line_capacity(services, products):
    """Calcula cuantas lineas distintas puede tener la venta."""
    service_capacity = 1 if services else 0
    product_capacity = len(products)
    return min(MAX_LINES, service_capacity + product_capacity)


def _increase_line_count(max_line_count=MAX_LINES):
    """Agrega una nueva linea al formulario."""
    current = _get_line_count()
    safe_max = max(1, min(int(max_line_count), MAX_LINES))
    st.session_state[LINE_COUNT_KEY] = min(current + 1, safe_max)


def _decrease_line_count():
    """Quita la ultima linea del formulario."""
    current = _get_line_count()
    st.session_state[LINE_COUNT_KEY] = max(current - 1, 1)


def _line_state_keys(index):
    """Lista las keys persistidas para una linea del formulario."""
    return (
        f"sales_item_type_{index}",
        f"sales_item_name_{index}",
        f"sales_item_qty_{index}",
        f"sales_item_price_{index}",
        f"sales_item_qty_display_{index}",
    )


def _remove_line_from_state(state, index):
    """Quita una linea intermedia y compacta el resto del estado."""
    line_count = int(state.get(LINE_COUNT_KEY, 1))
    if line_count <= 1:
        return

    if index < 0 or index >= line_count:
        return

    for current_index in range(index, line_count - 1):
        next_index = current_index + 1
        for current_key, next_key in zip(
            _line_state_keys(current_index),
            _line_state_keys(next_index),
        ):
            if next_key in state:
                state[current_key] = state[next_key]
            else:
                state.pop(current_key, None)

    for key in _line_state_keys(line_count - 1):
        state.pop(key, None)

    state[LINE_COUNT_KEY] = max(line_count - 1, 1)


def _remove_line(index):
    """Callback de Streamlit para quitar una linea especifica."""
    _remove_line_from_state(st.session_state, index)


def _clear_sales_form_state():
    """Limpia el estado de la UI de ventas al guardar exitosamente."""
    for key in list(st.session_state.keys()):
        if key.startswith("sales_"):
            st.session_state.pop(key, None)


def _selected_product_names_from_state(state, current_index, line_count):
    """Lista productos ya seleccionados en otras lineas."""
    selected = set()
    for index in range(line_count):
        if index == current_index:
            continue
        if state.get(f"sales_item_type_{index}") != "Producto":
            continue
        product_name = state.get(f"sales_item_name_{index}")
        if product_name:
            selected.add(product_name)
    return selected


def _get_product_options_for_line(products, state, current_index, line_count):
    """Devuelve productos disponibles para una linea sin repetir los ya usados."""
    selected_elsewhere = _selected_product_names_from_state(
        state,
        current_index,
        line_count,
    )
    return [
        product
        for product in products
        if product["name"] not in selected_elsewhere
    ]


def _service_selected_in_other_line_from_state(state, current_index, line_count):
    """Indica si otra linea ya usa el servicio principal."""
    for index in range(line_count):
        if index == current_index:
            continue
        if state.get(f"sales_item_type_{index}") == "Servicio":
            return True
    return False


def _service_selected_in_other_line(current_index):
    """Indica si otra linea ya usa el servicio principal."""
    return _service_selected_in_other_line_from_state(
        st.session_state,
        current_index,
        _get_line_count(),
    )


def _get_current_item_type_from_state(state, index, line_count):
    """Devuelve el tipo actual de una linea usando un default coherente."""
    key = f"sales_item_type_{index}"
    if key in state:
        return state[key]

    if _service_selected_in_other_line_from_state(state, index, line_count):
        return "Producto"

    return "Servicio"


def _get_item_type_options_for_line(
    state,
    index,
    line_count,
    services,
    product_options,
):
    """Devuelve tipos elegibles para una linea segun reglas de detalle."""
    current_type = state.get(f"sales_item_type_{index}")
    service_taken_elsewhere = _service_selected_in_other_line_from_state(
        state,
        index,
        line_count,
    )
    options = []

    if services and (not service_taken_elsewhere or current_type == "Servicio"):
        options.append("Servicio")

    if product_options:
        options.append("Producto")

    return tuple(options)


def _get_current_item_type(index):
    """Devuelve el tipo actual de una linea, usando un default coherente."""
    return _get_current_item_type_from_state(
        st.session_state,
        index,
        _get_line_count(),
    )


def render_sales_form():
    """Renderiza una primera UI nativa de ventas multi-item."""
    st.title("Registrar venta")

    lavanderia_id = st.session_state.get("lavanderia_id")
    user_id = st.session_state.get("user_id")

    if lavanderia_id is None or user_id is None:
        st.error("Hace falta una lavanderia y un usuario activos para registrar ventas.")
        return

    clients = _load_active_clients(lavanderia_id)
    generic_client, _billable_clients = _split_clients_for_sale(clients)
    services = get_active_services(lavanderia_id=lavanderia_id)
    products = get_active_products(lavanderia_id=lavanderia_id)
    vehicle_types = get_active_vehicle_types(lavanderia_id=lavanderia_id)

    if not services and not products:
        st.warning("No hay servicios ni productos activos para vender.")
        return

    st.subheader("Cobro")
    sale_date = st.date_input("Fecha *", value=date.today(), key="sales_date")
    payment_type = st.radio(
        "Tipo de cobro *",
        ["Contado", "Credito"],
        horizontal=True,
        key="sales_payment_type",
    )
    payment_method = st.selectbox("Metodo de pago", PAYMENT_METHODS, key="sales_payment_method")

    st.subheader("Vehiculo")
    vehicle_col, type_col = st.columns([2, 1])
    with vehicle_col:
        license_plate = st.text_input(
            "Matricula (opcional)",
            key="sales_license_plate",
            placeholder="Ej: ABC123",
        )
    vehicle_type_options = {vehicle_type["name"]: vehicle_type["id"] for vehicle_type in vehicle_types}
    with type_col:
        selected_vehicle_type_name = st.selectbox(
            "Tipo de vehiculo",
            options=list(vehicle_type_options.keys()) if vehicle_type_options else ["Sin tipos activos"],
            disabled=not bool(vehicle_type_options),
            key="sales_vehicle_type",
        )
    owner_col, phone_col = st.columns(2)
    with owner_col:
        owner_name = st.text_input(
            "Nombre del cliente (opcional)",
            key="sales_owner_name",
            placeholder="Ej: Juan Perez",
        )
    with phone_col:
        phone = st.text_input(
            "Telefono (opcional)",
            key="sales_phone",
            placeholder="Ej: 0981000000",
        )

    if license_plate.strip() and not vehicle_type_options:
        st.warning("No hay tipos de vehiculo activos para asociar esta matricula.")

    st.subheader("Factura")
    requires_invoice = st.checkbox("Generar factura", key="sales_requires_invoice")

    if requires_invoice:
        invoice_ruc_ci = st.text_input(
            "RUC/CI *",
            key="sales_invoice_ruc_ci",
            placeholder="Ej: 80012345-6 o 4567890",
        )
        invoice_razon_social = st.text_input(
            "Razon Social *",
            key="sales_invoice_razon_social",
            placeholder="Ej: Empresa SA o Juan Perez",
        )
        matched_client = _find_client_by_ruc_ci(clients, invoice_ruc_ci)
        if matched_client is not None:
            st.caption(
                f"Se reutilizará el cliente existente: {matched_client['name']} | "
                f"RUC/CI: {matched_client['ruc_ci']}"
            )
        elif invoice_ruc_ci.strip():
            st.caption(
                "Si el RUC/CI no existe todavía, se creará un cliente facturable "
                "al guardar esta venta."
            )
    else:
        invoice_ruc_ci = None
        invoice_razon_social = None
        if generic_client is not None:
            st.caption(f"Sin factura se usará {generic_client['name']} cuando la venta no tenga cliente por vehiculo.")

    sale_items = []
    current_total = Decimal("0.00")
    observation = st.text_area(
        "Observacion (opcional)",
        placeholder="Ej: venta mixta de lavado y productos",
        key="sales_observation",
    )

    st.divider()
    line_capacity = _get_available_line_capacity(services, products)
    if _get_line_count() > line_capacity:
        st.session_state[LINE_COUNT_KEY] = max(line_capacity, 1)

    header_col, add_col, remove_col = st.columns([3, 1, 1])
    with header_col:
        st.subheader("Detalle")
    with add_col:
        st.button(
            "Agregar línea",
            on_click=_increase_line_count,
            args=(line_capacity,),
            disabled=_get_line_count() >= line_capacity,
            use_container_width=True,
        )
    with remove_col:
        st.button(
            "Quitar última",
            on_click=_decrease_line_count,
            disabled=_get_line_count() <= 1,
            use_container_width=True,
        )

    line_count = _get_line_count()

    for index in range(line_count):
        title_col, remove_col = st.columns([5, 1])
        with title_col:
            st.markdown(f"**Línea {index + 1}**")
        with remove_col:
            st.button(
                "Quitar",
                key=f"sales_remove_line_{index}",
                on_click=_remove_line,
                args=(index,),
                disabled=line_count <= 1,
                use_container_width=True,
            )
        current_type = _get_current_item_type(index)
        product_options_for_line = _get_product_options_for_line(
            products,
            st.session_state,
            index,
            line_count,
        )
        item_type_options = _get_item_type_options_for_line(
            st.session_state,
            index,
            line_count,
            services,
            product_options_for_line,
        )
        if not item_type_options:
            st.warning("No hay mas servicios o productos disponibles para esta linea.")
            return

        item_type = st.selectbox(
            "Tipo",
            options=item_type_options,
            index=item_type_options.index(current_type) if current_type in item_type_options else 0,
            key=f"sales_item_type_{index}",
        )

        if item_type == "Servicio":
            if not services:
                st.warning("No hay servicios activos para agregar en esta venta.")
                return
            catalog = services
            item_key = "servicio_id"
            item_label = "Servicio *"
        else:
            catalog = product_options_for_line
            if not catalog:
                st.warning("No hay productos activos para agregar en esta venta.")
                return
            item_key = "producto_id"
            item_label = "Producto *"

        item_options = {item["name"]: item for item in catalog}
        selected_item_name = st.selectbox(
            item_label,
            options=list(item_options.keys()),
            key=f"sales_item_name_{index}",
        )

        if item_type == "Servicio":
            quantity = 1
            st.text_input(
                "Cantidad",
                value="1",
                disabled=True,
                key=f"sales_item_qty_display_{index}",
                help="La venta puede tener un solo servicio principal, y se registra una sola vez.",
            )
        else:
            quantity = st.number_input(
                "Cantidad",
                min_value=1,
                step=1,
                value=1,
                key=f"sales_item_qty_{index}",
            )

        selected_item = item_options[selected_item_name]
        suggested_price = Decimal(str(selected_item["price"]))
        edited_price = st.number_input(
            "Precio unitario",
            min_value=0.0,
            value=float(suggested_price),
            step=1000.0,
            format="%.0f",
            key=f"sales_item_price_{index}",
        )
        unit_price = Decimal(str(edited_price))
        subtotal = unit_price * quantity
        current_total += subtotal

        st.caption(
            f"Precio sugerido catálogo: {format_currency(suggested_price)} | "
            f"Subtotal: {format_currency(subtotal)}"
        )

        sale_payload = {
            "cantidad": int(quantity),
            "precio_unitario": float(unit_price),
            item_key: selected_item["id"],
        }
        sale_items.append(sale_payload)
        st.divider()

    st.info(f"Total estimado: {format_currency(current_total)}")

    submitted = st.button(
        "Guardar venta",
        type="primary",
        use_container_width=True,
    )

    if not submitted:
        return

    try:
        vehicle_payload = _build_vehicle_payload(
            license_plate,
            vehicle_type_options.get(selected_vehicle_type_name),
            owner_name,
            phone,
        )
        selected_vehicle_id = None
        if vehicle_payload is not None:
            selected_vehicle_id = find_or_create_vehicle(
                vehicle_payload["license_plate"],
                vehicle_payload["vehicle_type_id"],
                vehicle_payload["owner_name"],
                vehicle_payload["phone"],
                lavanderia_id=lavanderia_id,
            )

        sale_id = register_sale(
            lavanderia_id=lavanderia_id,
            usuario_id=user_id,
            cliente_id=None,
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
            f"Venta registrada #{sale_id} — "
            f"{normalize_plate(license_plate) if license_plate.strip() else 'Sin vehiculo'} — "
            f"{format_currency(current_total)}"
        )
        _clear_sales_form_state()
        st.rerun()
    except ValueError as error:
        st.error(str(error))
