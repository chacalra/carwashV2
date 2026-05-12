"""Servicios de reportes y resumen operativo orientados a ventas."""

from backend.repositories.expenses_repository import (
    get_expense_total_by_period,
    get_expenses_grouped_by_category,
)
from backend.repositories.sales_repository import (
    get_product_sales_count_by_period,
    get_product_sales_stats,
    get_sales_breakdown_by_item,
    get_sales_total_by_payment_type,
    get_sales_total_by_period,
    get_service_sales_count_by_period,
    get_service_sales_total_by_period,
    get_vehicle_sales_stats,
)


def get_sales_total(start_date, end_date, lavanderia_id=None):
    """Obtiene el total vendido para un periodo."""
    return get_sales_total_by_period(start_date, end_date, lavanderia_id=lavanderia_id)


def get_expense_total(start_date, end_date, lavanderia_id=None):
    """Obtiene el total de egresos para un periodo."""
    return get_expense_total_by_period(start_date, end_date, lavanderia_id=lavanderia_id)


def get_net_balance(start_date, end_date, lavanderia_id=None):
    """Calcula el balance neto del periodo."""
    sales_total = get_sales_total(start_date, end_date, lavanderia_id=lavanderia_id)
    expense_total = get_expense_total(start_date, end_date, lavanderia_id=lavanderia_id)
    return sales_total - expense_total


def get_sales_breakdown(start_date, end_date, lavanderia_id=None):
    """Devuelve el desglose de ventas por item."""
    return get_sales_breakdown_by_item(start_date, end_date, lavanderia_id=lavanderia_id)


def get_expense_breakdown(start_date, end_date, lavanderia_id=None):
    """Devuelve el desglose de egresos por categoria."""
    return get_expenses_grouped_by_category(start_date, end_date, lavanderia_id=lavanderia_id)


def get_service_count(start_date, end_date, lavanderia_id=None):
    """Cuenta cuantos servicios se registraron en el periodo."""
    return get_service_sales_count_by_period(start_date, end_date, lavanderia_id=lavanderia_id)


def get_product_count(start_date, end_date, lavanderia_id=None):
    """Cuenta cuantas ventas de productos se registraron en el periodo."""
    return get_product_sales_count_by_period(start_date, end_date, lavanderia_id=lavanderia_id)


def get_payment_type_summary(start_date, end_date, lavanderia_id=None):
    """Devuelve totales vendidos separados por tipo de cobro."""
    totals = get_sales_total_by_payment_type(start_date, end_date, lavanderia_id=lavanderia_id)
    return {
        "contado": totals.get("Contado", 0),
        "credito": totals.get("Credito", 0),
    }


def get_customer_summary(start_date, end_date, lavanderia_id=None):
    """Devuelve estadisticas de clientes: unicos, recurrentes, top 5 matriculas."""
    stats = get_vehicle_sales_stats(start_date, end_date, lavanderia_id=lavanderia_id)
    unique = len(stats)
    recurring = sum(1 for row in stats if row["visit_count"] > 1)
    return {
        "unique_vehicles": unique,
        "recurring_customers": recurring,
        "new_customers": unique - recurring,
        "top_plates": [dict(row) for row in stats[:5]],
    }


def get_product_summary(start_date, end_date, lavanderia_id=None):
    """Devuelve estadisticas de productos vendidos en el periodo."""
    stats = get_product_sales_stats(start_date, end_date, lavanderia_id=lavanderia_id)
    total_sales = sum(row["sale_count"] for row in stats)
    return {
        "total_sales": total_sales,
        "top_products": [dict(row) for row in stats[:5]],
    }


def get_sales_summary(start_date, end_date, lavanderia_id=None):
    """Construye un resumen operativo simple orientado a ventas."""
    sales_total = get_sales_total(start_date, end_date, lavanderia_id=lavanderia_id)
    expense_total = get_expense_total(start_date, end_date, lavanderia_id=lavanderia_id)
    service_sales_total = get_service_sales_total_by_period(
        start_date,
        end_date,
        lavanderia_id=lavanderia_id,
    )
    sales_breakdown = get_sales_breakdown(start_date, end_date, lavanderia_id=lavanderia_id)
    payment_breakdown = get_payment_type_summary(
        start_date,
        end_date,
        lavanderia_id=lavanderia_id,
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "sales_total": sales_total,
        "expense_total": expense_total,
        "net_balance": sales_total - expense_total,
        "service_count": get_service_count(start_date, end_date, lavanderia_id=lavanderia_id),
        "service_sales_total": service_sales_total,
        "product_count": get_product_count(start_date, end_date, lavanderia_id=lavanderia_id),
        "sales_breakdown": sales_breakdown,
        "expense_breakdown": get_expense_breakdown(
            start_date,
            end_date,
            lavanderia_id=lavanderia_id,
        ),
        "payment_breakdown": payment_breakdown,
    }
