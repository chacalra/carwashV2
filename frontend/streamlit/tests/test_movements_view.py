"""Tests para helpers de ui/movements_view.py."""

from frontend.streamlit.ui.movements_view import (
    _build_sales_dataframe,
    _filter_sales_dataframe,
    _format_concept_label,
    _get_billable_client_options,
)


def _sales_rows():
    return [
        {
            "id": 1,
            "date": "2026-05-04",
            "concepts": "Lavado x1 | Perfume x2",
            "client": "Consumidor Final",
            "vehicle": "ABC123",
            "total": 100000,
            "payment_type": "Contado",
            "payment_method": "Efectivo",
            "requires_invoice": False,
            "ruc_ci": None,
            "observation": "Sin novedad",
            "created_by": "admin",
        },
        {
            "id": 2,
            "date": "2026-05-04",
            "concepts": "Cera x1",
            "client": "Acme SA",
            "vehicle": "Sin vehiculo",
            "total": 30000,
            "payment_type": "Credito",
            "payment_method": "Transferencia",
            "requires_invoice": True,
            "ruc_ci": "80012345-6",
            "observation": None,
            "created_by": "cajero",
        },
    ]


def test_format_concept_label_includes_quantity():
    assert _format_concept_label("Perfume", 2) == "Perfume x2"


def test_build_sales_dataframe_formats_v2_sales_rows():
    df = _build_sales_dataframe(_sales_rows())

    assert list(df.columns) == [
        "Fecha",
        "Conceptos",
        "Cliente",
        "Vehiculo",
        "Total",
        "Tipo de cobro",
        "Metodo de pago",
        "Factura",
        "RUC/CI",
        "Observaciones",
        "Registrado por",
    ]
    assert df.loc[0, "Total"] == "Gs. 100.000"
    assert df.loc[0, "Factura"] == "No"
    assert df.loc[1, "Factura"] == "Si"


def test_filter_sales_dataframe_searches_concepts_client_and_vehicle():
    df = _build_sales_dataframe(_sales_rows())

    by_concept = _filter_sales_dataframe(df, search="perfume")
    by_client = _filter_sales_dataframe(df, search="acme")
    by_vehicle = _filter_sales_dataframe(df, search="abc")

    assert by_concept["Cliente"].tolist() == ["Consumidor Final"]
    assert by_client["Cliente"].tolist() == ["Acme SA"]
    assert by_vehicle["Vehiculo"].tolist() == ["ABC123"]


def test_filter_sales_dataframe_filters_or_excludes_billable_clients():
    df = _build_sales_dataframe(_sales_rows())

    only_acme = _filter_sales_dataframe(df, razon_social_filter=["Acme SA"])
    exclude_acme = _filter_sales_dataframe(
        df,
        razon_social_filter=["Acme SA"],
        exclude=True,
    )

    assert only_acme["Cliente"].tolist() == ["Acme SA"]
    assert exclude_acme["Cliente"].tolist() == ["Consumidor Final"]


def test_get_billable_client_options_uses_invoiced_sales_only():
    assert _get_billable_client_options(_sales_rows()) == ["Acme SA"]
