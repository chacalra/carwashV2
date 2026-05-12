"""Vista de dashboard operativo."""

from datetime import date

import pandas as pd
import streamlit as st

from backend.repositories.sales_repository import get_daily_sales
from backend.services.report_service import get_customer_summary, get_product_summary, get_sales_summary
from frontend.streamlit.utils.date_shortcuts import get_period_range, previous_period
from frontend.streamlit.utils.formatters import format_currency, format_number


def _section_title(label, accent=False):
    """Titulo de seccion en azul. accent=True agrega borde izquierdo para destacar."""
    if accent:
        st.markdown(
            f"<div style='border-left: 3px solid #1976D2; padding-left: 10px; margin-bottom: 4px;'>"
            f"<span style='color: #1976D2; font-size: 0.8rem; font-weight: 700; "
            f"text-transform: uppercase; letter-spacing: 0.07em'>{label}</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<span style='color: #1976D2; font-size: 0.8rem; font-weight: 600; "
            f"text-transform: uppercase; letter-spacing: 0.07em'>{label}</span>",
            unsafe_allow_html=True,
        )


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
    return period, start_date, end_date


def render_summary_cards(summary, prev_summary, payment_breakdown, show_delta=True):
    """Renderiza metricas principales agrupadas en containers con borde."""
    if show_delta:
        sales_delta = format_currency(summary["sales_total"] - prev_summary["sales_total"])
        expense_delta = format_currency(summary["expense_total"] - prev_summary["expense_total"])
        balance_delta = format_currency(summary["net_balance"] - prev_summary["net_balance"])
        count_delta = int(summary["service_count"] - prev_summary["service_count"])
        product_delta = int(summary["product_count"] - prev_summary["product_count"])
    else:
        sales_delta = expense_delta = balance_delta = count_delta = product_delta = None

    service_count = summary["service_count"]
    service_sales_total = summary["service_sales_total"]
    ticket_avg = service_sales_total / service_count if service_count > 0 else 0
    product_sales_total = summary["sales_total"] - service_sales_total

    if show_delta:
        prev_ticket = (
            prev_summary["service_sales_total"] / prev_summary["service_count"]
            if prev_summary["service_count"] > 0
            else 0
        )
        ticket_delta = format_currency(ticket_avg - prev_ticket)
        svc_sales_delta = format_currency(service_sales_total - prev_summary["service_sales_total"])
        prev_product_sales_total = prev_summary["sales_total"] - prev_summary["service_sales_total"]
        prd_sales_delta = format_currency(product_sales_total - prev_product_sales_total)
    else:
        ticket_delta = svc_sales_delta = prd_sales_delta = None

    _section_title("Resumen financiero", accent=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ventas", format_currency(summary["sales_total"]), delta=sales_delta)
    col2.metric("Contado", format_currency(payment_breakdown["contado"]))
    col3.metric("Credito", format_currency(payment_breakdown["credito"]))
    col4.metric("Balance", format_currency(summary["net_balance"]), delta=balance_delta)

    _section_title("Operaciones")
    col_svc, col_prd, col_ticket, col_expense = st.columns(4)
    with col_svc:
        st.metric("Lavados", format_number(service_count), delta=count_delta)
        st.metric("Servicios", format_currency(service_sales_total), delta=svc_sales_delta)
    with col_prd:
        st.metric("Productos", format_number(summary["product_count"]), delta=product_delta)
        st.metric("Venta productos", format_currency(product_sales_total), delta=prd_sales_delta)
    with col_ticket:
        st.metric("Ticket promedio", format_currency(ticket_avg), delta=ticket_delta)
    with col_expense:
        st.metric(
            "Egresos",
            format_currency(summary["expense_total"]),
            delta=expense_delta,
            delta_color="inverse",
        )


def render_trend_section(start_date, end_date, period):
    """Renderiza grafico de tendencia de ventas diarias. Se omite para 'Hoy'."""
    if period == "Hoy":
        return
    daily = get_daily_sales(str(start_date), str(end_date))
    if not daily or len(daily) < 2:
        return
    df = pd.DataFrame(daily)
    df["date"] = pd.to_datetime(df["date"])
    df = df.rename(columns={"total": "Ventas"})
    with st.container(border=True):
        st.subheader("Tendencia de ventas")
        st.vega_lite_chart(
            df,
            {
                "mark": {
                    "type": "bar",
                    "cornerRadiusTopLeft": 4,
                    "cornerRadiusTopRight": 4,
                    "color": "#1976D2",
                },
                "encoding": {
                    "x": {
                        "field": "date",
                        "type": "temporal",
                        "timeUnit": "yearmonthdate",
                        "axis": {"title": None, "format": "%d %b", "labelAngle": -45},
                        "scale": {"paddingInner": 0.2},
                    },
                    "y": {
                        "field": "Ventas",
                        "type": "quantitative",
                        "axis": {"title": None, "format": ",.0f"},
                    },
                    "tooltip": [
                        {"field": "date", "type": "temporal", "timeUnit": "yearmonthdate", "title": "Fecha", "format": "%d %b %Y"},
                        {"field": "Ventas", "type": "quantitative", "title": "Gs.", "format": ",.0f"},
                    ],
                },
                "config": {"view": {"stroke": "transparent"}},
            },
            use_container_width=True,
        )


def render_customer_section(start_date, end_date):
    """Renderiza seccion de estadisticas de clientes del periodo."""
    stats = get_customer_summary(str(start_date), str(end_date))
    if stats["unique_vehicles"] == 0:
        return

    with st.container(border=True):
        st.subheader("Clientes del periodo")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vehiculos unicos", stats["unique_vehicles"])
        c2.metric("Clientes recurrentes", stats["recurring_customers"])
        c3.metric("Clientes nuevos", stats["new_customers"])

        if stats["top_plates"]:
            with st.expander("Top 5 matriculas mas frecuentes"):
                top_df = pd.DataFrame(stats["top_plates"])
                col_map = {
                    "license_plate": "Matricula",
                    "vehicle_type": "Tipo",
                    "owner_name": "Dueno",
                    "visit_count": "Visitas",
                }
                display_cols = [c for c in col_map if c in top_df.columns]
                st.dataframe(
                    top_df[display_cols].rename(columns=col_map),
                    use_container_width=True,
                    hide_index=True,
                )


def render_product_section(start_date, end_date):
    """Renderiza seccion de estadisticas de productos vendidos en el periodo."""
    stats = get_product_summary(str(start_date), str(end_date))
    if stats["total_sales"] == 0:
        return

    with st.container(border=True):
        st.subheader("Productos vendidos")
        if stats["top_products"]:
            with st.expander("Top 5 productos mas vendidos"):
                top_df = pd.DataFrame(stats["top_products"])
                col_map = {
                    "name": "Producto",
                    "sale_count": "Ventas",
                    "total": "Total",
                }
                display_cols = [c for c in col_map if c in top_df.columns]
                st.dataframe(
                    top_df[display_cols].rename(columns=col_map).style.format(
                        {"Total": lambda v: format_currency(v)}
                    ),
                    use_container_width=True,
                    hide_index=True,
                )


def _donut_chart(df, tooltip_label):
    """Devuelve spec Vega-Lite para un grafico de torta/donut con porcentajes."""
    df = df.copy()
    total = df["total"].sum()
    df["pct"] = (df["total"] / total * 100).round(1) if total else 0
    spec = {
        "height": 300,
        "mark": {"type": "arc", "innerRadius": 70, "padAngle": 0.02},
        "encoding": {
            "theta": {"field": "total", "type": "quantitative", "stack": True},
            "color": {
                "field": "name",
                "type": "nominal",
                "legend": {"title": None, "orient": "bottom", "columns": 2},
                "scale": {"scheme": "tableau10"},
            },
            "tooltip": [
                {"field": "name", "type": "nominal", "title": tooltip_label},
                {"field": "total", "type": "quantitative", "title": "Gs.", "format": ",.0f"},
                {"field": "pct", "type": "quantitative", "title": "%", "format": ".1f"},
            ],
        },
        "config": {"view": {"stroke": None}},
    }
    return df, spec


def render_breakdown_charts(sales_df, expenses_df):
    """Renderiza graficos de torta para ventas y egresos con tabla de detalle en expander."""
    with st.container(border=True):
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Ventas por item")
            if not sales_df.empty and sales_df["total"].sum() > 0:
                df, spec = _donut_chart(sales_df, "Item")
                st.vega_lite_chart(df, spec, use_container_width=True)
                with st.expander("Ver tabla"):
                    display = sales_df.rename(columns={"name": "Item", "count": "Cantidad", "total": "Total"})
                    total_row = pd.DataFrame([{"Item": "Total", "Cantidad": int(display["Cantidad"].sum()), "Total": display["Total"].sum()}])
                    display = pd.concat([display, total_row], ignore_index=True)
                    st.dataframe(
                        display.style
                            .format({"Total": lambda v: format_currency(v)})
                            .apply(lambda x: ["font-weight: bold" if x.name == len(display) - 1 else "" for _ in x], axis=1),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.info("No hay ventas para graficar.")

        with right_col:
            st.subheader("Egresos por categoria")
            if not expenses_df.empty and expenses_df["total"].sum() > 0:
                df, spec = _donut_chart(expenses_df, "Categoria")
                st.vega_lite_chart(df, spec, use_container_width=True)
                with st.expander("Ver tabla"):
                    display = expenses_df.rename(columns={"name": "Categoria", "total": "Total"})
                    total_row = pd.DataFrame([{"Categoria": "Total", "Total": display["Total"].sum()}])
                    display = pd.concat([display, total_row], ignore_index=True)
                    st.dataframe(
                        display.style
                            .format({"Total": lambda v: format_currency(v)})
                            .apply(lambda x: ["font-weight: bold" if x.name == len(display) - 1 else "" for _ in x], axis=1),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.info("No hay egresos para graficar.")


def render_dashboard():
    """Renderiza el dashboard principal."""
    st.title("Dashboard operativo")

    period, start_date, end_date = _render_period_selector()

    summary = get_sales_summary(str(start_date), str(end_date))
    prev_start, prev_end = previous_period(start_date, end_date)
    prev_summary = get_sales_summary(str(prev_start), str(prev_end))

    sales_df = pd.DataFrame([dict(row) for row in summary["sales_breakdown"]])
    expenses_df = pd.DataFrame([dict(row) for row in summary["expense_breakdown"]])

    render_summary_cards(summary, prev_summary, summary["payment_breakdown"], show_delta=(period != "Personalizado"))
    render_trend_section(start_date, end_date, period)
    render_customer_section(start_date, end_date)
    render_product_section(start_date, end_date)
    render_breakdown_charts(sales_df, expenses_df)
