"""Vista para consultar ventas y egresos registrados."""

from datetime import date

import pandas as pd
import streamlit as st

from backend.database.connection import SessionLocal
from backend.database.schema import Cliente, Producto, Servicio, Usuario, Vehiculo
from backend.repositories.expenses_repository import get_expenses
from backend.repositories.sale_items_repository import list_sale_items
from backend.repositories.sales_repository import list_sales
from frontend.streamlit.utils.date_shortcuts import get_period_range
from frontend.streamlit.utils.formatters import format_currency, format_number

SALES_COLUMNS = {
    "date": "Fecha",
    "concepts": "Conceptos",
    "client": "Cliente",
    "vehicle": "Vehiculo",
    "total": "Total",
    "payment_type": "Tipo de cobro",
    "payment_method": "Metodo de pago",
    "requires_invoice": "Factura",
    "ruc_ci": "RUC/CI",
    "observation": "Observaciones",
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


def _format_concept_label(name, quantity):
    """Devuelve etiqueta compacta para una linea de venta."""
    return f"{name} x{quantity}"


def _build_concepts_label(session, sale_id):
    """Agrupa los detalles de una venta en una sola etiqueta."""
    labels = []
    for item in list_sale_items(session, sale_id):
        if item.servicio_id is not None:
            service = session.get(Servicio, item.servicio_id)
            if service is not None:
                labels.append(_format_concept_label(service.nombre_servicio, item.cantidad))
        elif item.producto_id is not None:
            product = session.get(Producto, item.producto_id)
            if product is not None:
                labels.append(_format_concept_label(product.nombre_producto, item.cantidad))
    return " | ".join(labels)


def _load_sales_rows(lavanderia_id, start_date, end_date):
    """Carga ventas V2 agrupadas por venta."""
    with SessionLocal() as session:
        sales = list_sales(
            session,
            lavanderia_id,
            start_date=start_date,
            end_date=end_date,
        )
        rows = []
        for sale in sales:
            client = session.get(Cliente, sale.cliente_id)
            vehicle = session.get(Vehiculo, sale.vehiculo_id) if sale.vehiculo_id else None
            user = session.get(Usuario, sale.usuario_id)
            rows.append(
                {
                    "id": sale.id,
                    "date": sale.fecha_venta,
                    "concepts": _build_concepts_label(session, sale.id),
                    "client": client.nombre if client is not None else "Cliente desconocido",
                    "vehicle": vehicle.matricula if vehicle is not None else "Sin vehiculo",
                    "total": float(sale.total),
                    "payment_type": sale.tipo_cobro,
                    "payment_method": sale.metodo_pago,
                    "requires_invoice": bool(sale.requiere_factura),
                    "ruc_ci": client.ruc_ci if sale.requiere_factura and client is not None else None,
                    "observation": sale.observacion,
                    "created_by": user.nombre_usuario if user is not None else None,
                }
            )
        return rows


def _build_sales_dataframe(sales):
    """Construye dataframe de ventas listo para mostrar."""
    df = pd.DataFrame(sales)
    if df.empty:
        return df

    display_cols = [column for column in SALES_COLUMNS if column in df.columns]
    display_df = df[display_cols].copy().rename(columns=SALES_COLUMNS)
    display_df["Total"] = display_df["Total"].apply(format_currency)
    display_df["Factura"] = display_df["Factura"].map({True: "Si", False: "No"})
    return display_df


def _filter_sales_dataframe(df, search="", razon_social_filter=None, exclude=False):
    """Aplica filtros visibles de la tabla de ventas."""
    filtered = df.copy()
    razon_social_filter = razon_social_filter or []

    if search.strip() and not filtered.empty:
        search_value = search.strip()
        mask = pd.Series(False, index=filtered.index)
        for column in ["Conceptos", "Cliente", "Vehiculo"]:
            if column in filtered.columns:
                mask |= filtered[column].fillna("").str.contains(search_value, case=False)
        filtered = filtered[mask]

    if razon_social_filter and "Cliente" in filtered.columns:
        if exclude:
            filtered = filtered[~filtered["Cliente"].isin(razon_social_filter)]
        else:
            filtered = filtered[filtered["Cliente"].isin(razon_social_filter)]

    return filtered


def _get_billable_client_options(sales):
    """Devuelve clientes facturables visibles en el rango."""
    return sorted(
        {
            sale["client"]
            for sale in sales
            if sale.get("requires_invoice") and sale.get("client")
        }
    )


def render_sales_table(start_date, end_date):
    """Renderiza la tabla V2 de ventas para un periodo."""
    lavanderia_id = st.session_state.get("lavanderia_id")
    if lavanderia_id is None:
        st.error("Hace falta una lavanderia activa para consultar ventas.")
        return

    sales = _load_sales_rows(lavanderia_id, start_date, end_date)

    st.subheader("Ventas")

    razones = _get_billable_client_options(sales)

    st.caption("Filtros")
    col_search, col_empresa = st.columns([2, 3])
    with col_search:
        search = st.text_input(
            "Buscar",
            key="sales_search",
            placeholder="Matricula, cliente o concepto",
        )
    with col_empresa:
        empresa_filter = st.multiselect(
            "Razon social",
            options=razones,
            key="sales_empresa_filter",
            placeholder="Todas",
        )
        if empresa_filter:
            excluir = st.checkbox(
                "Excluir seleccionados",
                key="sales_empresa_excluir",
                help="Marca esta opcion para ocultar las razones sociales seleccionadas en lugar de mostrar solo ellas",
            )
        else:
            excluir = False

    st.divider()

    if sales:
        sales_df = _build_sales_dataframe(sales)
        filtered_df = _filter_sales_dataframe(
            sales_df,
            search=search,
            razon_social_filter=empresa_filter,
            exclude=excluir,
        )

        if filtered_df.empty:
            st.info("Sin resultados para la busqueda.")
        else:
            st.dataframe(
                filtered_df,
                width='stretch',
                hide_index=True,
            )
            col_r, col_m, _ = st.columns([1, 1, 2])
            col_r.metric("Ventas", len(filtered_df))
            visible_ids = filtered_df.index
            visible_total = sum(sales[index]["total"] for index in visible_ids)
            col_m.metric("Monto total", format_currency(visible_total))
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
        render_sales_table(start_date, end_date)

    with tab2:
        render_expenses_table(start_date, end_date)
