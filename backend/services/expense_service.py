"""Reglas de negocio para egresos."""

from backend.repositories.expense_categories_repository import get_category_by_id
from backend.repositories.expenses_repository import (
    cancel_expense,
    create_expense,
    get_expense_by_id,
    update_expense,
)
from backend.utils.tenant_context import resolve_lavanderia_id


def validate_expense_data(date, category_id, amount, description, lavanderia_id=None):
    """Valida y normaliza los datos de un egreso."""
    target_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
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

    category = get_category_by_id(category_id, lavanderia_id=target_lavanderia_id)
    if category is None:
        raise ValueError("La categoria seleccionada no existe.")

    if not category["estado"]:
        raise ValueError("No se puede registrar un egreso con una categoria inactiva.")

    if amount is None or amount <= 0:
        raise ValueError("El monto del egreso debe ser mayor que cero.")

    return {
        "date": normalized_date,
        "category_id": category_id,
        "amount": amount,
        "description": normalized_description,
        "lavanderia_id": target_lavanderia_id,
    }


def register_expense(
    session,
    date,
    category_id,
    amount,
    description=None,
    created_by=None,
    has_iva=False,
    user_id=None,
    lavanderia_id=None,
):
    """Valida y registra un nuevo egreso."""
    validated_data = validate_expense_data(
        date,
        category_id,
        amount,
        description,
        lavanderia_id=lavanderia_id,
    )

    return create_expense(
        session,
        validated_data["date"],
        validated_data["category_id"],
        validated_data["amount"],
        validated_data["description"],
        created_by=created_by,
        has_iva=1 if has_iva else 0,
        lavanderia_id=validated_data["lavanderia_id"],
        user_id=user_id,
    )


def edit_expense(
    session,
    expense_id,
    date,
    category_id,
    amount,
    description=None,
    has_iva=False,
    lavanderia_id=None,
):
    """Valida y actualiza un egreso existente."""
    validated_data = validate_expense_data(
        date,
        category_id,
        amount,
        description,
        lavanderia_id=lavanderia_id,
    )

    update_expense(
        session,
        expense_id,
        validated_data["date"],
        validated_data["category_id"],
        validated_data["amount"],
        validated_data["description"],
        has_iva=1 if has_iva else 0,
        lavanderia_id=validated_data["lavanderia_id"],
    )
    return expense_id


def get_expense(expense_id, lavanderia_id=None):
    """Busca un egreso por id dentro de la lavanderia actual."""
    target_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    return get_expense_by_id(expense_id, lavanderia_id=target_lavanderia_id)


def remove_expense(session, expense_id, lavanderia_id=None):
    """Anula un egreso existente dentro de la lavanderia actual."""
    target_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    cancel_expense(session, expense_id, lavanderia_id=target_lavanderia_id)
