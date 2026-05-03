"""Vista de formulario para registrar ingresos."""

from datetime import date

import streamlit as st

from repositories.incomes_repository import get_last_income_by_vehicle
from repositories.products_repository import get_active_products
from repositories.services_repository import get_active_services
from repositories.vehicle_types_repository import get_active_vehicle_types
from repositories.vehicles_repository import find_vehicle_by_plate
from services.income_service import register_income
from services.vehicle_service import normalize_plate
from utils.formatters import format_currency
from utils.notifications import notify

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Tarjeta", "QR"]


def _on_plate_change():
    plate = st.session_state.get("plate_search", "").strip()
    if plate:
        found = find_vehicle_by_plate(normalize_plate(plate))
        if found:
            st.session_state["found_vehicle"] = dict(found)
            last = get_last_income_by_vehicle(found["id"])
            if last:
                st.session_state["last_income"] = dict(last)
                st.session_state["requires_invoice_cb"] = bool(last["requires_invoice"])
            else:
                st.session_state.pop("last_income", None)
        else:
            st.session_state["found_vehicle"] = None
            st.session_state.pop("last_income", None)
    else:
        st.session_state.pop("found_vehicle", None)
        st.session_state.pop("last_income", None)


def render_income_form():
    """Renderiza el formulario de alta de ingresos."""
    st.title("Registrar ingreso")

    vehicle_types = get_active_vehicle_types()

    # --- TIPO DE REGISTRO (carga catalogo correspondiente) ---

    st.markdown("""
    <style>
    div[data-testid="stRadio"] label p { font-size: 1.1rem; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)
    st.subheader("Tipo de registro")
    income_type = st.radio(
        "Tipo de registro",
        ["Servicio", "Producto"],
        horizontal=True,
        key="income_type_radio",
        label_visibility="collapsed",
    )
    is_vehicle = income_type == "Servicio"

    if is_vehicle:
        services = get_active_services()
        if not services:
            st.warning("No hay servicios activos. Configure al menos uno en Configuracion.")
            return
        item_options = {s["name"]: s["id"] for s in services}
        item_label = "Servicio *"
    else:
        products = get_active_products()
        if not products:
            st.warning("No hay productos activos. Configure al menos uno en Configuracion → Productos.")
            return
        item_options = {p["name"]: p["id"] for p in products}
        item_label = "Producto *"
    item_names = list(item_options.keys())

    if is_vehicle:
        if not vehicle_types:
            st.warning("No hay tipos de vehiculo activos. Configure al menos uno en Configuracion.")
            return
        vehicle_type_options = {vt["name"]: vt["id"] for vt in vehicle_types}
        vehicle_type_names = list(vehicle_type_options.keys())

    # --- MATRICULA (solo para lavados, on_change dispara busqueda automatica) ---
    found_vehicle = None
    last_income = None

    if is_vehicle:
        st.subheader("Vehiculo")
        st.text_input(
            "Matricula *",
            key="plate_search",
            placeholder="Ej: ABC123",
            on_change=_on_plate_change,
        )

        found_vehicle = st.session_state.get("found_vehicle")
        last_income = st.session_state.get("last_income")

        if found_vehicle:
            vt_name = found_vehicle.get("vehicle_type_name", "")
            st.success(f"Cliente recurrente: **{found_vehicle['license_plate']}** — {vt_name}")
        elif "found_vehicle" in st.session_state:
            st.info("Matricula no encontrada. Se creara un nuevo vehiculo al guardar.")

    # Defaults desde vehiculo conocido
    default_type_index = 0
    default_owner = ""
    default_phone = ""
    if found_vehicle:
        type_name = found_vehicle.get("vehicle_type_name", "")
        if type_name in vehicle_type_names:
            default_type_index = vehicle_type_names.index(type_name)
        default_owner = found_vehicle.get("owner_name") or ""
        default_phone = found_vehicle.get("phone") or ""

    # Defaults desde ultimo ingreso del vehiculo
    default_item_index = 0
    default_amount = 0
    default_payment_method_index = 0
    default_payment_type_index = 0  # Contado
    default_notes = ""
    default_ruc_ci = ""
    default_razon_social = ""

    if last_income:
        svc_name = last_income.get("service", "")
        if svc_name in item_names:
            default_item_index = item_names.index(svc_name)
        default_amount = int(last_income.get("amount") or 0)
        pm = last_income.get("payment_method") or ""
        if pm in PAYMENT_METHODS:
            default_payment_method_index = PAYMENT_METHODS.index(pm)
        if last_income.get("payment_type") == "Credito":
            default_payment_type_index = 1
        default_notes = last_income.get("notes") or ""
        default_ruc_ci = last_income.get("ruc_ci") or ""
        default_razon_social = last_income.get("razon_social") or ""

    # --- FACTURA (fuera del form — permite mostrar/ocultar campos condicionales) ---
    st.subheader("Factura")
    st.checkbox("Generar factura", key="requires_invoice_cb")

    # --- FORMULARIO PRINCIPAL ---
    with st.form("income_form", clear_on_submit=True):
        if is_vehicle:
            selected_vehicle_type = st.selectbox(
                "Tipo de vehiculo *",
                options=vehicle_type_names,
                index=default_type_index,
            )
            owner_name = st.text_input("Nombre del dueno (opcional)", value=default_owner)
            phone = st.text_input("Telefono (opcional)", value=default_phone)
            st.divider()
        else:
            selected_vehicle_type = None
            owner_name = None
            phone = None

        income_date = st.date_input("Fecha *", value=date.today())
        selected_item = st.selectbox(
            item_label,
            options=item_names,
            index=default_item_index,
        )
        amount = st.number_input("Monto *", min_value=0, step=1000, format="%d", value=default_amount)
        payment_type = st.radio(
            "Tipo de cobro *",
            ["Contado", "Credito"],
            horizontal=True,
            index=default_payment_type_index,
        )
        payment_method = st.selectbox(
            "Metodo de pago",
            options=PAYMENT_METHODS,
            index=default_payment_method_index,
        )
        notes = st.text_area(
            "Observaciones (opcional)",
            value=default_notes,
            placeholder="Ej: propina, servicio adicional, cliente preferente",
        )

        # Campos de factura (condicionales segun checkbox fuera del form)
        if st.session_state.get("requires_invoice_cb"):
            st.divider()
            st.markdown("**Datos de factura**")
            ruc_ci = st.text_input("RUC/CI *", value=default_ruc_ci, placeholder="Ej: 80012345-6 o 4567890")
            razon_social = st.text_input("Razon Social *", value=default_razon_social, placeholder="Ej: Empresa SA o Juan Perez")
        else:
            ruc_ci = ""
            razon_social = ""

        submitted = st.form_submit_button("Guardar ingreso")

    if submitted:
        license_plate = st.session_state.get("plate_search", "").strip() if is_vehicle else None
        try:
            if is_vehicle and not license_plate:
                raise ValueError("La matricula del vehiculo es obligatoria.")
            if amount <= 0:
                raise ValueError("El monto debe ser mayor a cero.")
            requires_invoice = bool(st.session_state.get("requires_invoice_cb"))
            with st.spinner("Guardando..."):
                register_income(
                    date=str(income_date),
                    service_id=item_options[selected_item] if is_vehicle else None,
                    product_id=item_options[selected_item] if not is_vehicle else None,
                    amount=float(amount),
                    payment_method=payment_method,
                    notes=notes,
                    license_plate=license_plate,
                    vehicle_type_id=vehicle_type_options[selected_vehicle_type] if selected_vehicle_type else None,
                    owner_name=owner_name,
                    phone=phone,
                    payment_type=payment_type,
                    requires_invoice=requires_invoice,
                    ruc_ci=ruc_ci,
                    razon_social=razon_social,
                    created_by=st.session_state.get("user_name"),
                )
            tipo = "credito" if payment_type == "Credito" else "contado"
            label = normalize_plate(license_plate) if license_plate else "Producto"
            notify(
                f"Guardado ({tipo}): {selected_item} — {label}"
                f" — {format_currency(amount)}"
            )
            st.session_state.pop("plate_search", None)
            st.session_state.pop("found_vehicle", None)
            st.session_state.pop("last_income", None)
            st.session_state.pop("requires_invoice_cb", None)
            st.rerun()
        except ValueError as error:
            st.error(str(error))
