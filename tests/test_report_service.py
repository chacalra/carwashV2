"""Tests para services/report_service.py."""

from services.report_service import (
    get_income_breakdown,
    get_income_total,
    get_net_balance,
    get_payment_type_summary,
    get_sales_breakdown,
    get_sales_summary,
    get_sales_total,
    get_summary,
)


def test_get_sales_total_reuses_period_total(monkeypatch):
    monkeypatch.setattr(
        "services.report_service.get_income_total_by_period",
        lambda start_date, end_date: 125000,
    )

    assert get_sales_total("2026-05-01", "2026-05-31") == 125000


def test_get_net_balance_uses_sales_total_and_expenses(monkeypatch):
    monkeypatch.setattr("services.report_service.get_sales_total", lambda *args: 300000)
    monkeypatch.setattr("services.report_service.get_expense_total", lambda *args: 90000)

    assert get_net_balance("2026-05-01", "2026-05-31") == 210000


def test_get_payment_type_summary_maps_known_values(monkeypatch):
    monkeypatch.setattr(
        "services.report_service.get_income_total_by_payment_type",
        lambda start_date, end_date: {"Contado": 100000, "Credito": 50000, "Otro": 1000},
    )

    assert get_payment_type_summary("2026-05-01", "2026-05-31") == {
        "contado": 100000,
        "credito": 50000,
    }


def test_get_sales_summary_exposes_native_and_legacy_keys(monkeypatch):
    monkeypatch.setattr("services.report_service.get_sales_total", lambda *args: 450000)
    monkeypatch.setattr("services.report_service.get_expense_total", lambda *args: 120000)
    monkeypatch.setattr("services.report_service.get_service_count", lambda *args: 8)
    monkeypatch.setattr("services.report_service.get_service_income_total", lambda *args: 300000)
    monkeypatch.setattr("services.report_service.get_product_count", lambda *args: 5)
    monkeypatch.setattr(
        "services.report_service.get_sales_breakdown",
        lambda *args: [{"name": "Lavado completo", "count": 3, "total": 200000}],
    )
    monkeypatch.setattr(
        "services.report_service.get_expense_breakdown",
        lambda *args: [{"name": "Insumos", "total": 120000}],
    )
    monkeypatch.setattr(
        "services.report_service.get_payment_type_summary",
        lambda *args: {"contado": 250000, "credito": 200000},
    )

    summary = get_sales_summary("2026-05-01", "2026-05-31")

    assert summary["sales_total"] == 450000
    assert summary["expense_total"] == 120000
    assert summary["net_balance"] == 330000
    assert summary["service_sales_total"] == 300000
    assert summary["sales_breakdown"] == [{"name": "Lavado completo", "count": 3, "total": 200000}]
    assert summary["payment_breakdown"] == {"contado": 250000, "credito": 200000}

    # Compatibilidad temporal
    assert summary["income_total"] == 450000
    assert summary["service_income_total"] == 300000
    assert summary["income_breakdown"] == [{"name": "Lavado completo", "count": 3, "total": 200000}]


def test_legacy_aliases_forward_to_sales_functions(monkeypatch):
    monkeypatch.setattr("services.report_service.get_sales_total", lambda *args: 111)
    monkeypatch.setattr("services.report_service.get_sales_breakdown", lambda *args: [{"name": "X"}])
    monkeypatch.setattr("services.report_service.get_sales_summary", lambda *args: {"sales_total": 111})

    assert get_income_total("2026-05-01", "2026-05-31") == 111
    assert get_income_breakdown("2026-05-01", "2026-05-31") == [{"name": "X"}]
    assert get_summary("2026-05-01", "2026-05-31") == {"sales_total": 111}
