"""Expense endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.deps import CurrentUser, DbSession, require_permission
from backend.api.routers._errors import raise_service_error
from backend.api.schemas.common import CreatedResponse, MessageResponse
from backend.api.schemas.expenses import ExpenseCreateRequest, ExpenseResponse
from backend.repositories.expenses_repository import get_expenses
from backend.services.expense_service import edit_expense, get_expense, register_expense, remove_expense


router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: CurrentUser = Depends(require_permission("movements")),
):
    """Lists expenses for a tenant."""
    return get_expenses(
        str(start_date) if start_date else None,
        str(end_date) if end_date else None,
        lavanderia_id=current_user.lavanderia_id,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense_detail(
    expense_id: int,
    current_user: CurrentUser = Depends(require_permission("movements")),
) -> ExpenseResponse:
    """Returns one expense by id."""
    expense = get_expense(expense_id, lavanderia_id=current_user.lavanderia_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El egreso indicado no existe.",
        )
    return expense


@router.post("", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreateRequest,
    db: DbSession,
    current_user: CurrentUser = Depends(require_permission("register_expense")),
) -> CreatedResponse:
    """Creates an expense."""
    if payload.usuario_id is not None and payload.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede registrar egresos en nombre de otro usuario.",
        )

    try:
        expense_id = register_expense(
            db,
            date=str(payload.fecha),
            category_id=payload.categoria_egreso_id,
            amount=payload.monto,
            description=payload.descripcion,
            user_id=current_user.id,
            lavanderia_id=current_user.lavanderia_id,
        )
    except ValueError as exc:
        raise_service_error(exc)

    return CreatedResponse(id=expense_id)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense_detail(
    expense_id: int,
    payload: ExpenseCreateRequest,
    db: DbSession,
    current_user: CurrentUser = Depends(require_permission("register_expense")),
) -> ExpenseResponse:
    """Updates an expense and returns the fresh document."""
    if payload.usuario_id is not None and payload.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede editar egresos en nombre de otro usuario.",
        )

    try:
        updated_expense_id = edit_expense(
            db,
            expense_id=expense_id,
            date=str(payload.fecha),
            category_id=payload.categoria_egreso_id,
            amount=payload.monto,
            description=payload.descripcion,
            lavanderia_id=current_user.lavanderia_id,
        )
    except ValueError as exc:
        raise_service_error(exc)

    expense = get_expense(updated_expense_id, lavanderia_id=current_user.lavanderia_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El egreso indicado no existe.",
        )
    return expense


@router.delete("/{expense_id}", response_model=MessageResponse)
def delete_expense_detail(
    expense_id: int,
    db: DbSession,
    current_user: CurrentUser = Depends(require_permission("register_expense")),
) -> MessageResponse:
    """Cancels an expense instead of deleting it permanently."""
    try:
        remove_expense(db, expense_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    return MessageResponse(message="Egreso anulado.")
