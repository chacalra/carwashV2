"""Vista para consultar ventas y egresos registrados."""

from datetime import date

import pandas as pd
import streamlit as st

from repositories.expenses_repository import get_expenses
from repositories.incomes_repository import get_incomes
from utils.date_shortcuts import get_period_range
from utils.formatters import format_number

SALES_COLUMNS = {
    "date": "Fecha",
    "service": "Servicio",
    "license_plate": "Matricula",
    "vehicle_type": "Tipo vehiculo",
    "owner_name": "Dueno",
    "amount": "Monto",
    "payment_type": "Tipo de cobro",
    "payment_method": "Metodo de pago",
    "ruc_ci": "RUC/CI",
    "razon_social": "Razon Social",
    "notes": "Observaciones",
    "created_by": "Registrado por",
}


def _render_period_selector():
    period = st.radio(
        "Periodo",
        ["Hoy", "Esta semana", "Este mes", "Personalizado"],
        horizontal=True,
        index=2,
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


def render_incomes_table(start_date, end_date):
    """Renderiza la tabla legacy de ventas para un periodo."""
    incomes = get_incomes(str(start_date), str(end_date))

    st.subheader("Ventas")

    if incomes:
        razones = sorted({dict(r)["razon_social"] for r in incomes if dict(r).get("razon_social")})
    else:
        razones = []

    st.caption("Filtros")
    col_search, col_empresa = st.columns([2, 3])
    with col_search:
        search = st.text_input(
            "Buscar por matricula o dueno",
            key="income_search",
            placeholder="Ej: ABC123 o Juan",
        )
    with col_empresa:
        empresa_filter = st.multiselect(
            "Razon social",
            options=razones,
            key="income_empresa_filter",
            placeholder="Todas",
        )
        if empresa_filter:
            excluir = st.checkbox(
                "Excluir seleccionados",
                key="income_empresa_excluir",
                help="Marca esta opcion para ocultar las razones sociales seleccionadas en lugar de mostrar solo ellas",
            )
        else:
            excluir = False

    st.divider()

    if incomes:
        incomes_df = pd.DataFrame([dict(row) for row in incomes])
        display_cols = [c for c in SALES_COLUMNS if c in incomes_df.columns]
        incomes_df = incomes_df[display_cols].rename(columns=SALES_COLUMNS)

        if search.strip():
            mask = pd.Series(False, index=incomes_df.index)
            for col in ["Matricula", "Dueno"]:
                if col in incomes_df.columns:
                    mask |= incomes_df[col].fillna("").str.contains(search.strip(), case=False)
            incomes_df = incomes_df[mask]

        if empresa_filter:
            if excluir:
                incomes_df = incomes_df[~incomes_df["Razon Social"].isin(empresa_filter)]
            else:
                incomes_df = incomes_df[incomes_df["Razon Social"].isin(empresa_filter)]

        if incomes_df.empty:
            st.info("Sin resultados para la busqueda.")
        else:
            st.dataframe(
                incomes_df.style.format({"Monto": lambda v: format_number(v)}),
                width='stretch',
                hide_index=True,
            )
            col_r, col_m, _ = st.columns([1, 1, 2])
            col_r.metric("Registros", len(incomes_df))
            col_m.metric("Monto total", f"Gs. {format_number(incomes_df['Monto'].sum())}")
    else:
        st.info("No hay ventas en el rango seleccionado.")


def render_expenses_table(start_date, end_date):
    """Renderiza la tabla de egresos para un periodo."""
    expenses = get_expenses(str(start_date), str(end_date))

    st.subheader("Egresos")
    if expenses:
        expenses_df = pd.DataFrame([dict(row) for row in expenses])
        EXPENSES_COLUMNS = {
            "date": "Fecha",
            "category": "Categoria",
            "amount": "Monto",
            "has_iva": "IVA",
            "description": "Descripcion",
            "created_by": "Registrado por",
        }
        display_cols = [c for c in EXPENSES_COLUMNS if c in expenses_df.columns]
        expenses_df = expenses_df[display_cols].rename(columns=EXPENSES_COLUMNS)
        if "IVA" in expenses_df.columns:
            expenses_df["IVA"] = expenses_df["IVA"].map({1: "Si", 0: "No"}).fillna("No")
        st.dataframe(
            expenses_df.style.format({"Monto": lambda v: format_number(v)}),
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No hay egresos en el rango seleccionado.")


def render_movements_view():
    """Renderiza la vista general de movimientos."""
    st.title("Movimientos")
    st.write("Consulta las ventas y egresos registrados por periodo.")

    start_date, end_date = _render_period_selector()

    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab"] { font-size: 1.1rem; font-weight: 600; padding: 10px 24px; }
    </style>
    """, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Ventas", "Egresos"])

    with tab1:
        render_incomes_table(start_date, end_date)

    with tab2:
        render_expenses_table(start_date, end_date)
