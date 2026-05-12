"""Tests para helpers de ui/sales_management_view.py."""

import pandas as pd

from frontend.streamlit.ui.sales_management_view import (
    _build_display_dataframe,
    _filter_sales,
    _format_sale_detail,
    _format_concept_label,
    _get_changed_payment_types,
    _get_selected_sale_ids,
    _sale_detail_options,
    _summarize_sales,
)


def _sales_rows():
    return [
        {
            "id": 1,
            "date": "2026-05-04",
            "concepts": "Lavado x1 | Perfume x2",
            "client": "Consumidor Final",
            "vehicle": "ABC123",
            "total": 70000,
            "payment_type": "Contado",
        },
        {
            "id": 2,
            "date": "2026-05-04",
            "concepts": "Cera x1",
            "client": "Acme SA",
            "vehicle": "Sin vehiculo",
            "total": 30000,
            "payment_type": "Credito",
        },
    ]


def test_format_concept_label_includes_quantity():
    assert _format_concept_label("Perfume", 2) == "Perfume x2"


def test_build_display_dataframe_formats_total_and_adds_void_column():
    display_df = _build_display_dataframe(_sales_rows())

    assert list(display_df.columns) == [
        "Anular",
        "id",
        "#",
        "Fecha",
        "Conceptos",
        "Cliente",
        "Vehiculo",
        "Total",
        "Tipo de cobro",
    ]
    assert display_df.loc[0, "Anular"] == False
    assert display_df.loc[0, "#"] == 1
    assert display_df.loc[0, "Total"] == "Gs. 70.000"


def test_get_changed_payment_types_returns_only_modified_rows():
    display_df = _build_display_dataframe(_sales_rows())
    edited_df = display_df.copy()
    edited_df.loc[0, "Tipo de cobro"] = "Credito"

    assert _get_changed_payment_types(display_df, edited_df) == [(1, "Credito")]


def test_get_selected_sale_ids_returns_checked_rows():
    display_df = _build_display_dataframe(_sales_rows())
    edited_df = display_df.copy()
    edited_df.loc[1, "Anular"] = True

    assert _get_selected_sale_ids(display_df, edited_df) == [2]


def test_summarize_sales_splits_cash_and_credit():
    summary = _summarize_sales(_sales_rows())

    assert summary == {
        "count": 2,
        "total": 100000,
        "cash_total": 70000,
        "credit_total": 30000,
    }


def test_sale_detail_options_builds_readable_labels():
    options = _sale_detail_options(_sales_rows())

    assert list(options.keys()) == [
        "#1 | 2026-05-04 | Consumidor Final | Gs. 70.000",
        "#2 | 2026-05-04 | Acme SA | Gs. 30.000",
    ]
    assert options["#1 | 2026-05-04 | Consumidor Final | Gs. 70.000"]["id"] == 1


def test_helpers_handle_empty_dataframes():
    empty_df = pd.DataFrame()

    assert _get_changed_payment_types(empty_df, empty_df) == []
    assert _get_selected_sale_ids(empty_df, empty_df) == []


def test_filter_sales_searches_id_concepts_client_and_vehicle():
    assert [sale["id"] for sale in _filter_sales(_sales_rows(), search="#1")] == [1]
    assert [sale["id"] for sale in _filter_sales(_sales_rows(), search="lavado")] == [1]
    assert [sale["id"] for sale in _filter_sales(_sales_rows(), search="acme")] == [2]
    assert [sale["id"] for sale in _filter_sales(_sales_rows(), search="abc")] == [1]


def test_filter_sales_filters_by_payment_type():
    assert [sale["id"] for sale in _filter_sales(_sales_rows(), payment_type="Credito")] == [2]
    assert [sale["id"] for sale in _filter_sales(_sales_rows(), payment_type="Contado")] == [1]


def test_format_sale_detail_returns_compact_detail():
    detail = _format_sale_detail(_sales_rows()[0])

    assert detail == {
        "Venta": "#1",
        "Cliente": "Consumidor Final",
        "Vehiculo": "ABC123",
        "Total": "Gs. 70.000",
        "Conceptos": "Lavado x1 | Perfume x2",
    }
