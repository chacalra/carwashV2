"""Helpers para calcular rangos de fecha por periodo."""

from datetime import date, timedelta


def get_period_range(period: str, today: date = None):
    """Devuelve (start_date, end_date) para un periodo nombrado."""
    today = today or date.today()
    if period == "Hoy":
        return today, today
    if period == "Esta semana":
        start = today - timedelta(days=today.weekday())
        return start, today
    if period == "Este mes":
        return today.replace(day=1), today
    return None, None


def previous_period(start_date: date, end_date: date):
    """Devuelve el periodo anterior de igual duracion."""
    duration = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=duration - 1)
    return prev_start, prev_end
