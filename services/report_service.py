"""Servicios de reportes y resumen operativo."""

from repositories.expenses_repository import (
    get_expense_total_by_period,
    get_expenses_grouped_by_category,
)
from repositories.incomes_repository import (
    get_customer_stats,
    get_income_count_by_period,
    get_income_grouped_by_service,
    get_income_total_by_payment_type,
    get_income_total_by_period,
    get_product_count_by_period,
    get_product_stats,
    get_service_income_total,
)


def get_income_total(start_date, end_date):
    """Obtiene el total de ingresos para un periodo."""
    return get_income_total_by_period(start_date, end_date)


def get_expense_total(start_date, end_date):
    """Obtiene el total de egresos para un periodo."""
    return get_expense_total_by_period(start_date, end_date)


def get_net_balance(start_date, end_date):
    """Calcula el balance neto del periodo."""
    income_total = get_income_total(start_date, end_date)
    expense_total = get_expense_total(start_date, end_date)
    return income_total - expense_total


def get_income_breakdown(start_date, end_date):
    """Devuelve el desglose de ingresos por servicio."""
    return get_income_grouped_by_service(start_date, end_date)


def get_expense_breakdown(start_date, end_date):
    """Devuelve el desglose de egresos por categoria."""
    return get_expenses_grouped_by_category(start_date, end_date)


def get_service_count(start_date, end_date):
    """Cuenta cuantos lavados (servicios) se registraron en el periodo."""
    return get_income_count_by_period(start_date, end_date)


def get_product_count(start_date, end_date):
    """Cuenta cuantas ventas de productos se registraron en el periodo."""
    return get_product_count_by_period(start_date, end_date)


def get_payment_type_summary(start_date, end_date):
    """Devuelve totales de ingresos separados por tipo de cobro."""
    totals = get_income_total_by_payment_type(start_date, end_date)
    return {
        "contado": totals.get("Contado", 0),
        "credito": totals.get("Credito", 0),
    }


def get_customer_summary(start_date, end_date):
    """Devuelve estadisticas de clientes: unicos, recurrentes, top 5 matriculas."""
    stats = get_customer_stats(start_date, end_date)
    unique = len(stats)
    recurring = sum(1 for row in stats if row["visit_count"] > 1)
    return {
        "unique_vehicles": unique,
        "recurring_customers": recurring,
        "new_customers": unique - recurring,
        "top_plates": [dict(row) for row in stats[:5]],
    }


def get_product_summary(start_date, end_date):
    """Devuelve estadisticas de productos vendidos en el periodo."""
    stats = get_product_stats(start_date, end_date)
    total_sales = sum(row["sale_count"] for row in stats)
    return {
        "total_sales": total_sales,
        "top_products": [dict(row) for row in stats[:5]],
    }


def get_summary(start_date, end_date):
    """Construye un resumen operativo simple para la UI."""
    income_total = get_income_total(start_date, end_date)
    expense_total = get_expense_total(start_date, end_date)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "income_total": income_total,
        "expense_total": expense_total,
        "net_balance": income_total - expense_total,
        "service_count": get_service_count(start_date, end_date),
        "service_income_total": get_service_income_total(start_date, end_date),
        "product_count": get_product_count(start_date, end_date),
        "income_breakdown": get_income_breakdown(start_date, end_date),
        "expense_breakdown": get_expense_breakdown(start_date, end_date),
        "payment_breakdown": get_payment_type_summary(start_date, end_date),
    }
