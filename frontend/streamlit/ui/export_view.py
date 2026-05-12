"""Vista para exportar datos del sistema."""

from datetime import date

import pandas as pd
import streamlit as st

from backend.repositories.expenses_repository import get_expenses
from backend.repositories.sales_repository import get_sales_export_rows
from backend.services.report_service import get_sales_summary
from frontend.streamlit.utils.date_shortcuts import get_period_range
from frontend.streamlit.utils.export import (
    build_export_filename,
    export_dataframe_to_csv,
    export_dataframe_to_excel,
)


def _rows_to_dataframe(rows):
    """Convierte filas serializadas en un DataFrame de pandas."""
    return pd.DataFrame([dict(row) for row in rows])


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
            start_date = st.date_input("Desde", value=date.today().replace(day=1))
        with col2:
            end_date = st.date_input("Hasta", value=date.today())
    else:
        start_date, end_date = get_period_range(period)
    return start_date, end_date


def render_csv_export(start_date, end_date):
    """Renderiza opciones de descarga CSV."""
    sales_df = _rows_to_dataframe(get_sales_export_rows(str(start_date), str(end_date)))
    expenses_df = _rows_to_dataframe(get_expenses(str(start_date), str(end_date)))

    col1, col2 = st.columns(2)

    with col1:
        if not sales_df.empty:
            st.download_button(
                label="Descargar ventas CSV",
                data=export_dataframe_to_csv(sales_df),
                file_name=build_export_filename("ventas", start_date, end_date, "csv"),
                mime="text/csv",
            )
        else:
            st.info("No hay ventas para exportar en CSV.")

    with col2:
        if not expenses_df.empty:
            st.download_button(
                label="Descargar egresos CSV",
                data=export_dataframe_to_csv(expenses_df),
                file_name=build_export_filename("egresos", start_date, end_date, "csv"),
                mime="text/csv",
            )
        else:
            st.info("No hay egresos para exportar en CSV.")


def render_excel_export(start_date, end_date):
    """Renderiza opcion de descarga Excel consolidada."""
    sales_df = _rows_to_dataframe(get_sales_export_rows(str(start_date), str(end_date)))
    expenses_df = _rows_to_dataframe(get_expenses(str(start_date), str(end_date)))
    summary = get_sales_summary(str(start_date), str(end_date))

    summary_df = pd.DataFrame(
        [
            {
                "desde": summary["start_date"],
                "hasta": summary["end_date"],
                "total_ventas": summary["sales_total"],
                "total_egresos": summary["expense_total"],
                "balance_neto": summary["net_balance"],
                "cantidad_servicios": summary["service_count"],
            }
        ]
    )

    excel_data = export_dataframe_to_excel(
        {
            "Resumen": summary_df,
            "Ventas": sales_df,
            "Egresos": expenses_df,
        }
    )

    st.download_button(
        label="Descargar reporte Excel",
        data=excel_data,
        file_name=build_export_filename("reporte_carwash", start_date, end_date, "xlsx"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_export_view():
    """Renderiza la vista principal de exportacion."""
    st.title("Exportar datos")
    st.write("Descarga ventas, egresos y un resumen del periodo seleccionado.")

    start_date, end_date = _render_period_selector()

    st.subheader("Exportacion CSV")
    render_csv_export(start_date, end_date)

    st.divider()
    st.subheader("Exportacion Excel")
    render_excel_export(start_date, end_date)
