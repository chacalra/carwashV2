"""Vista para gestionar ingresos: editar tipo de cobro y anular registros."""

from datetime import date

import pandas as pd
import streamlit as st

from repositories.incomes_repository import get_incomes, update_income_payment_type
from services.income_service import remove_income
from utils.date_shortcuts import get_period_range
from utils.formatters import format_currency

DISPLAY_COLUMNS = {
    "date": "Fecha",
    "service": "Servicio / Producto",
    "license_plate": "Matricula",
    "amount": "Monto",
    "payment_type": "Tipo de cobro",
    "created_by": "Registrado por",
}

PAYMENT_TYPES = ["Contado", "Credito"]


def _render_period_selector():
    period = st.radio(
        "Periodo",
        ["Hoy", "Esta semana", "Este mes", "Personalizado"],
        horizontal=True,
        index=1,
    )
    if period == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Desde", value=date.today().replace(day=1))
        with col2:
            end = st.date_input("Hasta", value=date.today())
    else:
        start, end = get_period_range(period)
    return start, end


def render_void_incomes_view():
    """Renderiza la vista de gestion de ingresos."""
    st.title("Gestionar ingresos")
    st.write("Edita el tipo de cobro directamente en la tabla o selecciona registros para anular.")

    start_date, end_date = _render_period_selector()

    incomes = get_incomes(str(start_date), str(end_date))

    if not incomes:
        st.info("No hay ingresos en el rango seleccionado.")
        return

    df = pd.DataFrame([dict(row) for row in incomes])
    display_cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    display_df = df[["id"] + display_cols].copy()
    display_df = display_df.rename(columns=DISPLAY_COLUMNS)
    display_df["Monto"] = display_df["Monto"].apply(
        lambda v: format_currency(float(v)) if v is not None else ""
    )
    display_df.insert(0, "Anular", False)

    edited = st.data_editor(
        display_df,
        key=f"void_editor_{start_date}_{end_date}",
        width='stretch',
        hide_index=True,
        column_config={
            "Anular": st.column_config.CheckboxColumn("Anular", default=False),
            "id": None,
            "Tipo de cobro": st.column_config.SelectboxColumn(
                "Tipo de cobro",
                options=PAYMENT_TYPES,
                required=True,
            ),
            "Monto": st.column_config.TextColumn("Monto"),
        },
        disabled=[c for c in display_df.columns if c not in ("Anular", "Tipo de cobro")],
    )

    # --- Cambios en tipo de cobro ---
    changed_mask = edited["Tipo de cobro"] != display_df["Tipo de cobro"]
    changed_ids = display_df.loc[changed_mask, "id"].tolist()
    changed_types = edited.loc[changed_mask, "Tipo de cobro"].tolist()

    if changed_ids:
        st.info(f"{len(changed_ids)} registro(s) con tipo de cobro modificado.")
        if st.button("Guardar cambios", type="primary"):
            for income_id, payment_type in zip(changed_ids, changed_types):
                update_income_payment_type(income_id, payment_type)
            st.success(f"{len(changed_ids)} registro(s) actualizado(s).")
            st.rerun()

    # --- Anulacion ---
    selected_ids = display_df.loc[edited["Anular"], "id"].tolist()

    if not selected_ids:
        return

    st.warning(f"{len(selected_ids)} ingreso(s) seleccionado(s) para anular.")

    confirm_key = "confirm_void"

    if st.session_state.get(confirm_key):
        st.error(f"¿Confirmar anulacion de {len(selected_ids)} ingreso(s)? Esta accion no se puede deshacer.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Si, anular", type="primary"):
                for income_id in selected_ids:
                    remove_income(income_id)
                st.session_state.pop(confirm_key, None)
                st.success(f"{len(selected_ids)} ingreso(s) anulado(s) correctamente.")
                st.rerun()
        with col2:
            if st.button("Cancelar"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
    else:
        if st.button("Anular seleccionados"):
            st.session_state[confirm_key] = True
            st.rerun()
