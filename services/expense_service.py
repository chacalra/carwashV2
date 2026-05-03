"""Reglas de negocio para egresos."""

from datetime import datetime

from repositories.expense_categories_repository import get_category_by_id
from repositories.expenses_repository import (
    create_expense,
    delete_expense,
    update_expense,
)


def validate_expense_data(date, category_id, amount, description):
    """Valida y normaliza los datos de un egreso."""
    normalized_date = date.strip() if isinstance(date, str) else ""
    normalized_description = (
        description.strip()
        if isinstance(description, str) and description.strip()
        else None
    )

    if not normalized_date:
        raise ValueError("La fecha del egreso es obligatoria.")

    if category_id is None:
        raise ValueError("La categoria del egreso es obligatoria.")

    category = get_category_by_id(category_id)
    if category is None:
        raise ValueError("La categoria seleccionada no existe.")

    if category["is_active"] != 1:
        raise ValueError("No se puede registrar un egreso con una categoria inactiva.")

    if amount is None or amount <= 0:
        raise ValueError("El monto del egreso debe ser mayor que cero.")

    return {
        "date": normalized_date,
        "category_id": category_id,
        "amount": amount,
        "description": normalized_description,
    }


def register_expense(date, category_id, amount, description=None, created_by=None, has_iva=False):
    """Valida y registra un nuevo egreso."""
    validated_data = validate_expense_data(
        date,
        category_id,
        amount,
        description,
    )
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return create_expense(
        validated_data["date"],
        validated_data["category_id"],
        validated_data["amount"],
        validated_data["description"],
        created_at,
        created_by=created_by,
        has_iva=1 if has_iva else 0,
    )


def edit_expense(expense_id, date, category_id, amount, description=None, has_iva=False):
    """Valida y actualiza un egreso existente."""
    validated_data = validate_expense_data(
        date,
        category_id,
        amount,
        description,
    )

    update_expense(
        expense_id,
        validated_data["date"],
        validated_data["category_id"],
        validated_data["amount"],
        validated_data["description"],
        has_iva=1 if has_iva else 0,
    )


def remove_expense(expense_id):
    """Elimina un egreso existente."""
    delete_expense(expense_id)
