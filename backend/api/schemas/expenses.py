"""Schemas for expense endpoints."""

from datetime import date, datetime

from pydantic import BaseModel


class ExpenseCreateRequest(BaseModel):
    """Create expense request."""

    usuario_id: int | None = None
    fecha: date
    categoria_egreso_id: int
    monto: float
    descripcion: str | None = None


class ExpenseResponse(BaseModel):
    """Expense response."""

    id: int
    date: date
    category_id: int
    category: str | None = None
    amount: float
    description: str | None = None
    created_by: str | None = None
    user_id: int
    created_at: datetime | None = None
    lavanderia_id: int
    estado: bool
