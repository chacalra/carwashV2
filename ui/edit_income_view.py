"""Vista para editar ingresos del dia actual y del dia anterior."""

from datetime import date, timedelta

import streamlit as st

from repositories.incomes_repository import get_income_by_id, get_incomes
from repositories.products_repository import get_active_products
from repositories.services_repository import get_active_services
from repositories.vehicle_types_repository import get_active_vehicle_types
from services.income_service import edit_income
from utils.formatters import format_currency
from utils.notifications import notify

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Tarjeta", "QR"]


def _income_label(income):
    plate = income["license_plate"] or "Sin matricula"
    return f"{income['date']} | {income['service']} | {plate} | {format_currency(income['amount'])}"


def _on_invoice_change():
    pass  # solo dispara rerun para mostrar/ocultar campos


def render_edit_income_view():
    """Renderiza la vista de edicion de ingresos (hoy y ayer)."""
    st.title("Editar ingreso")
    st.caption("Solo se pueden editar ingresos registrados hoy o ayer.")

    today = date.today()
    yesterday = today - timedelta(days=1)

    incomes = get_incomes(str(yesterday), str(today))
    if not incomes:
        st.info("No hay ingresos de hoy ni de ayer para editar.")
        return

    income_options = {_income_label(i): i["id"] for i in incomes}

    selected_label = st.selectbox(
        "Seleccionar ingreso a editar",
        list(income_options.keys()),
        key="edit_income_select",
    )
    income_id = income_options[selected_label]
    income = get_income_by_id(income_id)

    if income is None:
        st.error("No se pudo cargar el ingreso seleccionado.")
        return

    is_vehicle_income = income.get("service_id") is not None

    if is_vehicle_income:
        catalog_items = get_active_services()
        if not catalog_items:
            st.warning("No hay servicios activos para editar este ingreso.")
            return
        item_label = "Servicio *"
    else:
        catalog_items = get_active_products()
        if not catalog_items:
            st.warning("No hay productos activos para editar este ingreso.")
            return
        item_label = "Producto *"

    item_options = {item["name"]: item["id"] for item in catalog_items}
    item_names = list(item_options.keys())

    current_item_name = income["service"]
    current_item_id = income["service_id"] if is_vehicle_income else income["product_id"]
    if current_item_name and current_item_name not in item_options and current_item_id is not None:
        item_options[current_item_name] = current_item_id
        item_names.append(current_item_name)

    default_item_index = 0
    if current_item_name in item_names:
        default_item_index = item_names.index(current_item_name)

    vehicle_type_options = {}
    vehicle_type_names = []
    default_vt_index = 0

    if is_vehicle_income:
        vehicle_types = get_active_vehicle_types()
        if not vehicle_types:
            st.warning("No hay tipos de vehiculo activos para editar este ingreso.")
            return

        vehicle_type_options = {vt["name"]: vt["id"] for vt in vehicle_types}
        vehicle_type_names = list(vehicle_type_options.keys())

        if income["vehicle_type"] and income["vehicle_type"] not in vehicle_type_options and income.get("vehicle_type_id") is not None:
            vehicle_type_options[income["vehicle_type"]] = income["vehicle_type_id"]
            vehicle_type_names.append(income["vehicle_type"])

        if income["vehicle_type"] and income["vehicle_type"] in vehicle_type_names:
            default_vt_index = vehicle_type_names.index(income["vehicle_type"])

    default_pm_index = 0
    if income["payment_method"] and income["payment_method"] in PAYMENT_METHODS:
        default_pm_index = PAYMENT_METHODS.index(income["payment_method"])

    default_pt_index = 1 if income["payment_type"] == "Credito" else 0

    # Inicializar checkbox de factura en session_state si aun no esta seteado para este ingreso
    invoice_key = f"edit_invoice_cb_{income_id}"
    if invoice_key not in st.session_state:
        st.session_state[invoice_key] = bool(income["requires_invoice"])

    # --- Campos bloqueados (solo lectura) ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Fecha (no editable)", value=str(income["date"]), disabled=True)
    with col2:
        st.text_input(
            "Matricula (no editable)",
            value=income["license_plate"] or "Sin matricula",
            disabled=True,
        )

    # --- Checkbox factura fuera del form ---
    st.checkbox("Generar factura", key=invoice_key)

    # --- Formulario de edicion ---
    with st.form(f"edit_income_form_{income_id}"):
        if is_vehicle_income:
            selected_vt = st.selectbox(
                "Tipo de vehiculo *",
                options=vehicle_type_names,
                index=default_vt_index,
            )
            owner_name = st.text_input(
                "Nombre del dueno (opcional)",
                value=income["owner_name"] or "",
            )
            phone = st.text_input(
                "Telefono (opcional)",
                value=income["phone"] or "",
            )
            st.divider()
        else:
            selected_vt = None
            owner_name = None
            phone = None

        selected_item = st.selectbox(
            item_label,
            options=item_names,
            index=default_item_index,
        )
        st.text_input(
            "Monto (no editable)",
            value=format_currency(income["amount"]),
            disabled=True,
        )
        amount = income["amount"]
        payment_type = st.radio(
            "Tipo de cobro *",
            ["Contado", "Credito"],
            horizontal=True,
            index=default_pt_index,
        )
        payment_method = st.selectbox(
            "Metodo de pago",
            options=PAYMENT_METHODS,
            index=default_pm_index,
        )
        notes = st.text_area(
            "Observaciones (opcional)",
            value=income["notes"] or "",
            placeholder="Ej: propina, servicio adicional, cliente preferente",
        )

        if st.session_state.get(invoice_key):
            st.divider()
            st.markdown("**Datos de factura**")
            ruc_ci = st.text_input(
                "RUC/CI *",
                value=income["ruc_ci"] or "",
                placeholder="Ej: 80012345-6 o 4567890",
            )
            razon_social = st.text_input(
                "Razon Social *",
                value=income["razon_social"] or "",
                placeholder="Ej: Empresa SA o Juan Perez",
            )
        else:
            ruc_ci = ""
            razon_social = ""

        submitted = st.form_submit_button("Guardar cambios", type="primary")

    if submitted:
        try:
            requires_invoice = bool(st.session_state.get(invoice_key))
            with st.spinner("Guardando..."):
                edit_income(
                    income_id=income_id,
                    date=str(income["date"]),
                    service_id=item_options[selected_item] if is_vehicle_income else None,
                    product_id=item_options[selected_item] if not is_vehicle_income else None,
                    amount=float(amount),
                    payment_method=payment_method,
                    notes=notes,
                    license_plate=income["license_plate"],
                    vehicle_type_id=vehicle_type_options[selected_vt] if selected_vt else None,
                    owner_name=owner_name,
                    phone=phone,
                    payment_type=payment_type,
                    requires_invoice=requires_invoice,
                    ruc_ci=ruc_ci,
                    razon_social=razon_social,
                )
            st.session_state.pop(invoice_key, None)
            st.session_state.pop("edit_income_select", None)
            notify(f"Ingreso actualizado: {selected_item} — {format_currency(amount)}")
            st.rerun()
        except ValueError as error:
            st.error(str(error))
