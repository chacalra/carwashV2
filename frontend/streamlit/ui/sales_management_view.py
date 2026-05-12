"""Vista nativa para gestionar ventas recientes."""

from datetime import date

import pandas as pd
import streamlit as st

from backend.database.connection import SessionLocal
from backend.database.schema import Cliente, Producto, Servicio, Vehiculo
from backend.repositories.sale_items_repository import list_sale_items
from backend.repositories.sales_repository import list_sales
from backend.services.sale_service import remove_sale, update_sale_payment_type
from frontend.streamlit.utils.date_shortcuts import get_period_range
from frontend.streamlit.utils.formatters import format_currency

DISPLAY_COLUMNS = {
    "date": "Fecha",
    "concepts": "Conceptos",
    "client": "Cliente",
    "vehicle": "Vehiculo",
    "total": "Total",
    "payment_type": "Tipo de cobro",
}

PAYMENT_TYPES = ["Contado", "Credito"]


def _format_concept_label(name, quantity):
    """Devuelve una etiqueta compacta para una linea de venta."""
    return f"{name} x{quantity}"


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


def _build_concepts_label(session, sale_id):
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
            rows.append(
                {
                    "id": sale.id,
                    "date": sale.fecha_venta,
                    "concepts": _build_concepts_label(session, sale.id),
                    "client": client.nombre if client is not None else "Cliente desconocido",
                    "vehicle": vehicle.matricula if vehicle is not None else "Sin vehiculo",
                    "total": float(sale.total),
                    "payment_type": sale.tipo_cobro,
                }
            )
        return rows


def _build_display_dataframe(sales):
    """Construye la tabla editable que ve el usuario."""
    df = pd.DataFrame(sales)
    if df.empty:
        return df

    display_cols = [column for column in DISPLAY_COLUMNS if column in df.columns]
    display_df = df[["id"] + display_cols].copy().rename(columns=DISPLAY_COLUMNS)
    display_df.insert(1, "#", display_df["id"])
    display_df["Total"] = display_df["Total"].apply(format_currency)
    display_df.insert(0, "Anular", False)
    return display_df


def _get_changed_payment_types(display_df, edited_df):
    """Devuelve pares venta_id/tipo cuando el usuario cambio el tipo de cobro."""
    if display_df.empty or edited_df.empty:
        return []

    original = display_df.set_index("id")
    edited = edited_df.set_index("id")
    changes = []

    for sale_id in original.index:
        original_type = original.at[sale_id, "Tipo de cobro"]
        edited_type = edited.at[sale_id, "Tipo de cobro"]
        if edited_type != original_type:
            changes.append((int(sale_id), edited_type))

    return changes


def _get_selected_sale_ids(display_df, edited_df):
    """Devuelve ids marcados para anular."""
    if display_df.empty or edited_df.empty:
        return []

    selected = edited_df.loc[edited_df["Anular"], "id"].tolist()
    return [int(sale_id) for sale_id in selected]


def _summarize_sales(sales):
    """Calcula metricas simples del rango visible."""
    total = sum(float(sale["total"]) for sale in sales)
    credit_total = sum(
        float(sale["total"])
        for sale in sales
        if sale["payment_type"] == "Credito"
    )
    cash_total = total - credit_total
    return {
        "count": len(sales),
        "total": total,
        "cash_total": cash_total,
        "credit_total": credit_total,
    }


def _sale_detail_options(sales):
    """Construye opciones legibles para consultar el detalle de una venta."""
    return {
        (
            f"#{sale['id']} | {sale['date']} | {sale['client']} | "
            f"{format_currency(sale['total'])}"
        ): sale
        for sale in sales
    }


def _filter_sales(sales, search="", payment_type="Todos"):
    """Filtra ventas por texto y tipo de cobro."""
    filtered = sales
    normalized_search = search.strip().lower() if isinstance(search, str) else ""

    if normalized_search:
        if normalized_search.startswith("#"):
            sale_number = normalized_search.removeprefix("#")
            filtered = [
                sale
                for sale in filtered
                if str(sale["id"]) == sale_number
            ]
        else:
            filtered = [
                sale
                for sale in filtered
                if normalized_search in str(sale["concepts"]).lower()
                or normalized_search in str(sale["client"]).lower()
                or normalized_search in str(sale["vehicle"]).lower()
            ]

    if payment_type != "Todos":
        filtered = [
            sale
            for sale in filtered
            if sale["payment_type"] == payment_type
        ]

    return filtered


def _format_sale_detail(sale):
    """Devuelve lineas compactas para leer el detalle de una venta."""
    return {
        "Venta": f"#{sale['id']}",
        "Cliente": sale["client"],
        "Vehiculo": sale["vehicle"],
        "Total": format_currency(sale["total"]),
        "Conceptos": sale["concepts"] or "Sin conceptos cargados",
    }


def render_sales_management_view():
    """Renderiza la vista de gestion de ventas."""
    st.title("Gestionar ventas")

    lavanderia_id = st.session_state.get("lavanderia_id")
    if lavanderia_id is None:
        st.error("Hace falta una lavanderia activa para gestionar ventas.")
        return

    start_date, end_date = _render_period_selector()
    sales = _load_sales_rows(lavanderia_id, start_date, end_date)

    if not sales:
        st.info("No hay ventas en el rango seleccionado.")
        return

    filter_col, payment_col = st.columns([3, 1])
    with filter_col:
        search = st.text_input(
            "Buscar",
            key=f"sales_management_search_{start_date}_{end_date}",
            placeholder="Venta, cliente, matricula o concepto",
        )
    with payment_col:
        payment_filter = st.selectbox(
            "Tipo de cobro",
            options=["Todos"] + PAYMENT_TYPES,
            key=f"sales_management_payment_filter_{start_date}_{end_date}",
        )

    filtered_sales = _filter_sales(
        sales,
        search=search,
        payment_type=payment_filter,
    )

    if not filtered_sales:
        st.info("Sin ventas para los filtros seleccionados.")
        return

    summary = _summarize_sales(filtered_sales)
    metric_count, metric_total, metric_cash, metric_credit = st.columns(4)
    metric_count.metric("Ventas", summary["count"])
    metric_total.metric("Total", format_currency(summary["total"]))
    metric_cash.metric("Contado", format_currency(summary["cash_total"]))
    metric_credit.metric("Credito", format_currency(summary["credit_total"]))

    table_col, detail_col = st.columns([3, 1])
    display_df = _build_display_dataframe(filtered_sales)

    with table_col:
        edited = st.data_editor(
            display_df,
            key=f"sales_management_editor_{start_date}_{end_date}_{search}_{payment_filter}",
            width="stretch",
            hide_index=True,
            column_config={
                "Anular": st.column_config.CheckboxColumn("Anular", default=False),
                "#": st.column_config.NumberColumn("#", width="small"),
                "id": None,
                "Tipo de cobro": st.column_config.SelectboxColumn(
                    "Tipo de cobro",
                    options=PAYMENT_TYPES,
                    required=True,
                ),
                "Total": st.column_config.TextColumn("Total"),
            },
            disabled=[
                column
                for column in display_df.columns
                if column not in ("Anular", "Tipo de cobro")
            ],
        )

    with detail_col:
        st.subheader("Detalle")
        detail_options = _sale_detail_options(filtered_sales)
        selected_detail_label = st.selectbox(
            "Venta",
            options=list(detail_options.keys()),
            key=f"sales_management_detail_{start_date}_{end_date}_{search}_{payment_filter}",
            label_visibility="collapsed",
        )
        selected_sale = detail_options[selected_detail_label]
        detail = _format_sale_detail(selected_sale)
        st.markdown(f"**{detail['Venta']}**")
        st.caption(detail["Cliente"])
        st.caption(detail["Vehiculo"])
        st.metric("Total", detail["Total"])
        st.write(detail["Conceptos"])

    st.divider()

    payment_changes = _get_changed_payment_types(display_df, edited)

    if payment_changes:
        st.info(f"{len(payment_changes)} venta(s) con tipo de cobro modificado.")
        if st.button("Guardar cambios", type="primary"):
            try:
                for sale_id, payment_type in payment_changes:
                    update_sale_payment_type(
                        lavanderia_id=lavanderia_id,
                        sale_id=sale_id,
                        tipo_cobro=payment_type,
                    )
                st.success(f"{len(payment_changes)} venta(s) actualizada(s).")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    selected_ids = _get_selected_sale_ids(display_df, edited)
    if not selected_ids:
        return

    st.warning(f"{len(selected_ids)} venta(s) seleccionada(s) para anular.")

    confirm_key = "confirm_void_sales"
    if st.session_state.get(confirm_key):
        st.error(
            f"¿Confirmar anulacion de {len(selected_ids)} venta(s)? "
            "Esta accion no se puede deshacer."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Si, anular", type="primary"):
                try:
                    for sale_id in selected_ids:
                        remove_sale(lavanderia_id=lavanderia_id, sale_id=sale_id)
                    st.session_state.pop(confirm_key, None)
                    st.success(f"{len(selected_ids)} venta(s) anulada(s) correctamente.")
                    st.rerun()
                except ValueError as error:
                    st.session_state.pop(confirm_key, None)
                    st.error(str(error))
        with col2:
            if st.button("Cancelar"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
    else:
        if st.button("Anular seleccionadas"):
            st.session_state[confirm_key] = True
            st.rerun()
