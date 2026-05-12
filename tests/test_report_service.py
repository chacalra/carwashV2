"""Tests para services/report_service.py."""

from backend.services.report_service import (
    get_net_balance,
    get_payment_type_summary,
    get_sales_breakdown,
    get_sales_summary,
    get_sales_total,
)


def test_get_sales_total_reuses_period_total(monkeypatch):
    monkeypatch.setattr(
        "backend.services.report_service.get_sales_total_by_period",
        lambda start_date, end_date, **kwargs: 125000,
    )

    assert get_sales_total("2026-05-01", "2026-05-31") == 125000


def test_get_net_balance_uses_sales_total_and_expenses(monkeypatch):
    monkeypatch.setattr("backend.services.report_service.get_sales_total", lambda *args, **kwargs: 300000)
    monkeypatch.setattr("backend.services.report_service.get_expense_total", lambda *args, **kwargs: 90000)

    assert get_net_balance("2026-05-01", "2026-05-31") == 210000


def test_get_payment_type_summary_maps_known_values(monkeypatch):
    monkeypatch.setattr(
        "backend.services.report_service.get_sales_total_by_payment_type",
        lambda start_date, end_date, **kwargs: {"Contado": 100000, "Credito": 50000, "Otro": 1000},
    )

    assert get_payment_type_summary("2026-05-01", "2026-05-31") == {
        "contado": 100000,
        "credito": 50000,
    }


def test_get_sales_summary_exposes_native_keys(monkeypatch):
    monkeypatch.setattr("backend.services.report_service.get_sales_total", lambda *args, **kwargs: 450000)
    monkeypatch.setattr("backend.services.report_service.get_expense_total", lambda *args, **kwargs: 120000)
    monkeypatch.setattr("backend.services.report_service.get_service_count", lambda *args, **kwargs: 8)
    monkeypatch.setattr("backend.services.report_service.get_service_sales_total_by_period", lambda *args, **kwargs: 300000)
    monkeypatch.setattr("backend.services.report_service.get_product_count", lambda *args, **kwargs: 5)
    monkeypatch.setattr(
        "backend.services.report_service.get_sales_breakdown",
        lambda *args, **kwargs: [{"name": "Lavado completo", "count": 3, "total": 200000}],
    )
    monkeypatch.setattr(
        "backend.services.report_service.get_expense_breakdown",
        lambda *args, **kwargs: [{"name": "Insumos", "total": 120000}],
    )
    monkeypatch.setattr(
        "backend.services.report_service.get_payment_type_summary",
        lambda *args, **kwargs: {"contado": 250000, "credito": 200000},
    )

    summary = get_sales_summary("2026-05-01", "2026-05-31")

    assert summary["sales_total"] == 450000
    assert summary["expense_total"] == 120000
    assert summary["net_balance"] == 330000
    assert summary["service_sales_total"] == 300000
    assert summary["sales_breakdown"] == [{"name": "Lavado completo", "count": 3, "total": 200000}]
    assert summary["payment_breakdown"] == {"contado": 250000, "credito": 200000}
