"""Vista de dashboard operativo."""

from datetime import date

import pandas as pd
import streamlit as st

from repositories.incomes_repository import get_daily_incomes, get_income_detail_by_razon_social, get_income_grouped_by_razon_social
from utils.formatters import is_company_name
from services.report_service import get_customer_summary, get_product_summary, get_summary
from utils.date_shortcuts import get_period_range, previous_period
from utils.formatters import format_currency, format_number


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
        income_delta = format_currency(summary["income_total"] - prev_summary["income_total"])
        expense_delta = format_currency(summary["expense_total"] - prev_summary["expense_total"])
        balance_delta = format_currency(summary["net_balance"] - prev_summary["net_balance"])
        count_delta = int(summary["service_count"] - prev_summary["service_count"])
        product_delta = int(summary["product_count"] - prev_summary["product_count"])
    else:
        income_delta = expense_delta = balance_delta = count_delta = product_delta = None

    with st.container(border=True):
        _section_title("Resumen financiero", accent=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Ingresos", format_currency(summary["income_total"]), delta=income_delta)
        col2.metric(
            "Egresos",
            format_currency(summary["expense_total"]),
            delta=expense_delta,
            delta_color="inverse",
        )
        col3.metric("Balance neto", format_currency(summary["net_balance"]), delta=balance_delta)

        if payment_breakdown.get("credito", 0) > 0:
            _section_title("Desglose por tipo de cobro")
            c1, c2 = st.columns(2)
            c1.metric("Contado", format_currency(payment_breakdown["contado"]))
            c2.metric("Credito (pendiente de cobro)", format_currency(payment_breakdown["credito"]))

    with st.container(border=True):
        _section_title("Operaciones")
        ticket_avg = summary["service_income_total"] / summary["service_count"] if summary["service_count"] > 0 else 0
        product_income = summary["income_total"] - summary["service_income_total"]
        if show_delta:
            prev_ticket = prev_summary["service_income_total"] / prev_summary["service_count"] if prev_summary["service_count"] > 0 else 0
            ticket_delta = format_currency(ticket_avg - prev_ticket)
            svc_income_delta = format_currency(summary["service_income_total"] - prev_summary["service_income_total"])
            prev_product_income = prev_summary["income_total"] - prev_summary["service_income_total"]
            prd_income_delta = format_currency(product_income - prev_product_income)
        else:
            ticket_delta = svc_income_delta = prd_income_delta = None
        col_svc, col_prd, col_ticket = st.columns(3)
        with col_svc:
            st.metric("Lavados realizados", format_number(summary["service_count"]), delta=count_delta)
            st.metric("Ingresos servicios", format_currency(summary["service_income_total"]), delta=svc_income_delta)
        with col_prd:
            st.metric("Productos vendidos", format_number(summary["product_count"]), delta=product_delta)
            st.metric("Ingresos productos", format_currency(product_income), delta=prd_income_delta)
        with col_ticket:
            st.metric("Ticket promedio", format_currency(ticket_avg), delta=ticket_delta)


def render_trend_section(start_date, end_date, period):
    """Renderiza grafico de tendencia de ingresos diarios. Se omite para 'Hoy'."""
    if period == "Hoy":
        return
    daily = get_daily_incomes(str(start_date), str(end_date))
    if not daily or len(daily) < 2:
        return
    df = pd.DataFrame(daily)
    df["date"] = pd.to_datetime(df["date"])
    df = df.rename(columns={"total": "Ingresos"})
    with st.container(border=True):
        st.subheader("Tendencia de ingresos")
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
                        "field": "Ingresos",
                        "type": "quantitative",
                        "axis": {"title": None, "format": ",.0f"},
                    },
                    "tooltip": [
                        {"field": "date", "type": "temporal", "timeUnit": "yearmonthdate", "title": "Fecha", "format": "%d %b %Y"},
                        {"field": "Ingresos", "type": "quantitative", "title": "Gs.", "format": ",.0f"},
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


def _render_empresa_subsection(grupos, start_str, end_str, key_suffix):
    """Renderiza tabla resumen + selector de detalle para un grupo de empresas."""
    resumen_df = pd.DataFrame(grupos)
    resumen_df = resumen_df.rename(columns={
        "razon_social": "Empresa",
        "ruc_ci": "RUC/CI",
        "count": "Registros",
        "total": "Total",
    })
    resumen_df["Total"] = resumen_df["Total"].apply(format_currency)
    st.dataframe(resumen_df, use_container_width=True, hide_index=True)

    empresas = [g["razon_social"] for g in grupos]
    selected = st.selectbox("Ver detalle", ["— Seleccionar —"] + empresas, key=f"select_empresa_{key_suffix}")

    if selected and selected != "— Seleccionar —":
        detalle = get_income_detail_by_razon_social(start_str, end_str, selected)
        if detalle:
            detalle_df = pd.DataFrame(detalle)
            detalle_df = detalle_df.rename(columns={
                "date": "Fecha",
                "service": "Servicio",
                "vehicle_type": "Tipo",
                "amount": "Monto",
            })
            detalle_df["Monto"] = detalle_df["Monto"].apply(format_currency)
            st.dataframe(detalle_df, use_container_width=True, hide_index=True)


def render_empresa_section(start_date, end_date):
    """Renderiza secciones de ingresos por empresa separadas por servicios y productos."""
    start_str = str(start_date)
    end_str = str(end_date)
    key = f"{start_str}_{end_str}"

    servicios = [g for g in get_income_grouped_by_razon_social(start_str, end_str, income_type="service") if is_company_name(g["razon_social"])]
    productos = [g for g in get_income_grouped_by_razon_social(start_str, end_str, income_type="product") if is_company_name(g["razon_social"])]

    if not servicios and not productos:
        return

    if servicios:
        with st.container(border=True):
            st.subheader("Ingresos servicios por empresa")
            _render_empresa_subsection(servicios, start_str, end_str, f"svc_{key}")

    if productos:
        with st.container(border=True):
            st.subheader("Ingresos productos por empresa")
            _render_empresa_subsection(productos, start_str, end_str, f"prd_{key}")


def _donut_chart(df, tooltip_label):
    """Devuelve spec Vega-Lite para un grafico de torta/donut con porcentajes."""
    df = df.copy()
    df["pct"] = (df["total"] / df["total"].sum() * 100).round(1)
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


def render_breakdown_charts(incomes_df, expenses_df):
    """Renderiza graficos de torta para ingresos y egresos con tabla de detalle en expander."""
    with st.container(border=True):
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Ingresos por servicio")
            if not incomes_df.empty:
                df, spec = _donut_chart(incomes_df, "Servicio")
                st.vega_lite_chart(df, spec, use_container_width=True)
                with st.expander("Ver tabla"):
                    display = incomes_df.rename(columns={"name": "Servicio", "count": "Cantidad", "total": "Total"})
                    total_row = pd.DataFrame([{"Servicio": "Total", "Cantidad": int(display["Cantidad"].sum()), "Total": display["Total"].sum()}])
                    display = pd.concat([display, total_row], ignore_index=True)
                    st.dataframe(
                        display.style
                            .format({"Total": lambda v: format_currency(v)})
                            .apply(lambda x: ["font-weight: bold" if x.name == len(display) - 1 else "" for _ in x], axis=1),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.info("No hay ingresos para graficar.")

        with right_col:
            st.subheader("Egresos por categoria")
            if not expenses_df.empty:
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

    with st.container(border=True):
        period, start_date, end_date = _render_period_selector()

    summary = get_summary(str(start_date), str(end_date))
    prev_start, prev_end = previous_period(start_date, end_date)
    prev_summary = get_summary(str(prev_start), str(prev_end))

    incomes_df = pd.DataFrame([dict(row) for row in summary["income_breakdown"]])
    expenses_df = pd.DataFrame([dict(row) for row in summary["expense_breakdown"]])

    render_summary_cards(summary, prev_summary, summary["payment_breakdown"], show_delta=(period != "Personalizado"))
    render_trend_section(start_date, end_date, period)
    render_customer_section(start_date, end_date)
    render_product_section(start_date, end_date)
    render_empresa_section(start_date, end_date)
    render_breakdown_charts(incomes_df, expenses_df)
