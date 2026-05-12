"""Tests para helpers de ui/sales_edit_view.py."""

from decimal import Decimal

from frontend.streamlit.ui.sales_edit_view import (
    _build_detail_dataframe,
    _build_existing_sale_items_payload,
    _build_sale_item_payload,
    _calculate_items_total,
    _ensure_invoice_state,
    _invoice_key,
)


def _sale_items():
    return [
        {
            "type": "Servicio",
            "concept_id": 8,
            "concept_name": "Lavado",
            "quantity": 1,
            "unit_price": Decimal("40000.00"),
        },
        {
            "type": "Producto",
            "concept_id": 4,
            "concept_name": "Perfume",
            "quantity": 2,
            "unit_price": Decimal("30000.00"),
        },
    ]


def test_build_sale_item_payload_uses_correct_foreign_key():
    product_payload = _build_sale_item_payload("Producto", 4, 2, 15000)
    service_payload = _build_sale_item_payload("Servicio", 8, 1, 50000)

    assert product_payload == {
        "cantidad": 2,
        "precio_unitario": 15000.0,
        "producto_id": 4,
    }
    assert service_payload == {
        "cantidad": 1,
        "precio_unitario": 50000.0,
        "servicio_id": 8,
    }


def test_build_existing_sale_items_payload_preserves_lines():
    payload = _build_existing_sale_items_payload(_sale_items())

    assert payload == [
        {
            "cantidad": 1,
            "precio_unitario": 40000.0,
            "servicio_id": 8,
        },
        {
            "cantidad": 2,
            "precio_unitario": 30000.0,
            "producto_id": 4,
        },
    ]


def test_build_detail_dataframe_formats_read_only_detail():
    df = _build_detail_dataframe(_sale_items())

    assert list(df.columns) == [
        "Tipo",
        "Concepto",
        "Cantidad",
        "Precio unitario",
        "Subtotal",
    ]
    assert df.loc[0, "Concepto"] == "Lavado"
    assert df.loc[0, "Subtotal"] == "Gs. 40.000"
    assert df.loc[1, "Cantidad"] == 2
    assert df.loc[1, "Subtotal"] == "Gs. 60.000"


def test_calculate_items_total_sums_subtotals():
    assert _calculate_items_total(_sale_items()) == Decimal("100000.00")


def test_ensure_invoice_state_initializes_without_overwriting_user_change():
    state = {}
    key = _ensure_invoice_state(state, 7, True)

    assert key == _invoice_key(7)
    assert state[key] is True

    state[key] = False
    _ensure_invoice_state(state, 7, True)

    assert state[key] is False
