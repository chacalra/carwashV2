"""Vista de formulario para registrar egresos."""

from datetime import date

import streamlit as st

from backend.repositories.expense_categories_repository import get_active_categories
from backend.services.expense_service import register_expense
from frontend.streamlit.utils.formatters import format_currency
from frontend.streamlit.utils.notifications import notify


def render_expense_form():
    """Renderiza el formulario de alta de egresos."""
    st.title("Registrar egreso")

    categories = get_active_categories()
    if not categories:
        st.warning("No hay categorias activas disponibles.")
        return

    category_options = {category["name"]: category["id"] for category in categories}

    with st.form("expense_form", clear_on_submit=True):
        expense_date = st.date_input("Fecha *", value=date.today())
        selected_category = st.selectbox("Categoria *", options=list(category_options.keys()))
        amount = st.number_input("Monto *", min_value=0, step=1000, format="%d")
        description = st.text_area(
            "Descripcion (opcional)",
            placeholder="Ej: combustible, mantenimiento, insumos de limpieza",
        )
        has_iva = st.checkbox("IVA")
        submitted = st.form_submit_button("Guardar egreso")

    if submitted:
        try:
            if amount <= 0:
                raise ValueError("El monto debe ser mayor a cero.")
            with st.spinner("Guardando..."):
                register_expense(
                    date=str(expense_date),
                    category_id=category_options[selected_category],
                    amount=float(amount),
                    description=description,
                    created_by=st.session_state.get("user_name"),
                    user_id=st.session_state.get("user_id"),
                    has_iva=has_iva,
                )
            notify(f"Guardado: {selected_category} — {format_currency(amount)}")
            st.rerun()
        except ValueError as error:
            st.error(str(error))
