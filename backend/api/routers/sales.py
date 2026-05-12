"""Sale endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.deps import CurrentUser, require_permission
from backend.api.routers._errors import raise_service_error
from backend.api.schemas.common import CreatedResponse, MessageResponse
from backend.api.schemas.sales import (
    SaleCreateRequest,
    SaleExportRow,
    SalePaymentTypeRequest,
    SaleResponse,
)
from backend.repositories.sales_repository import get_grouped_sale_by_id, get_sales_export_rows, get_sales_grouped
from backend.services.sale_service import (
    edit_sale,
    register_sale,
    remove_sale,
    update_sale_payment_type,
)


router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=list[SaleExportRow])
def list_sales(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: CurrentUser = Depends(require_permission("movements")),
):
    """Lists flattened sales rows for a tenant."""
    return get_sales_export_rows(
        str(start_date) if start_date else None,
        str(end_date) if end_date else None,
        lavanderia_id=current_user.lavanderia_id,
    )


@router.get("/grouped", response_model=list[SaleResponse])
def list_sales_grouped(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: CurrentUser = Depends(require_permission("movements")),
):
    """Lists grouped sales with nested detail lines for a tenant."""
    return get_sales_grouped(
        str(start_date) if start_date else None,
        str(end_date) if end_date else None,
        lavanderia_id=current_user.lavanderia_id,
    )


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    current_user: CurrentUser = Depends(require_permission("movements")),
):
    """Returns a grouped sale by id."""
    sale = get_grouped_sale_by_id(sale_id, lavanderia_id=current_user.lavanderia_id)
    if sale is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La venta indicada no existe en esta lavanderia.",
        )
    return sale


@router.post("", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreateRequest,
    current_user: CurrentUser = Depends(require_permission("register_sale")),
) -> CreatedResponse:
    """Creates a sale with one or more detail lines."""
    if payload.usuario_id is not None and payload.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede registrar ventas en nombre de otro usuario.",
        )

    try:
        sale_id = register_sale(
            lavanderia_id=current_user.lavanderia_id,
            usuario_id=current_user.id,
            fecha_venta=payload.fecha_venta,
            tipo_cobro=payload.tipo_cobro,
            items=[item.model_dump(exclude_none=True) for item in payload.items],
            cliente_id=payload.cliente_id,
            metodo_pago=payload.metodo_pago,
            requiere_factura=payload.requiere_factura,
            observacion=payload.observacion,
            vehiculo_id=payload.vehiculo_id,
            ruc_ci=payload.ruc_ci,
            razon_social=payload.razon_social,
        )
    except ValueError as exc:
        raise_service_error(exc)

    return CreatedResponse(id=sale_id)


@router.put("/{sale_id}", response_model=SaleResponse)
def update_sale(
    sale_id: int,
    payload: SaleCreateRequest,
    current_user: CurrentUser = Depends(require_permission("edit_sale")),
) -> SaleResponse:
    """Updates a sale and returns the grouped document."""
    if payload.usuario_id is not None and payload.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede editar ventas en nombre de otro usuario.",
        )

    try:
        updated_sale_id = edit_sale(
            lavanderia_id=current_user.lavanderia_id,
            sale_id=sale_id,
            usuario_id=current_user.id,
            fecha_venta=payload.fecha_venta,
            tipo_cobro=payload.tipo_cobro,
            items=[item.model_dump(exclude_none=True) for item in payload.items],
            cliente_id=payload.cliente_id,
            metodo_pago=payload.metodo_pago,
            requiere_factura=payload.requiere_factura,
            observacion=payload.observacion,
            vehiculo_id=payload.vehiculo_id,
            ruc_ci=payload.ruc_ci,
            razon_social=payload.razon_social,
        )
    except ValueError as exc:
        raise_service_error(exc)

    return get_grouped_sale_by_id(updated_sale_id, lavanderia_id=current_user.lavanderia_id)


@router.patch("/{sale_id}/payment-type", response_model=MessageResponse)
def update_payment_type(
    sale_id: int,
    payload: SalePaymentTypeRequest,
    current_user: CurrentUser = Depends(require_permission("edit_sale")),
) -> MessageResponse:
    """Updates a sale payment type."""
    try:
        update_sale_payment_type(current_user.lavanderia_id, sale_id, payload.tipo_cobro)
    except ValueError as exc:
        raise_service_error(exc)
    return MessageResponse(message="Venta actualizada.")


@router.delete("/{sale_id}", response_model=MessageResponse)
def delete_sale(
    sale_id: int,
    current_user: CurrentUser = Depends(require_permission("manage_sales")),
) -> MessageResponse:
    """Voids a sale logically instead of deleting it permanently."""
    try:
        remove_sale(current_user.lavanderia_id, sale_id)
    except ValueError as exc:
        raise_service_error(exc)
    return MessageResponse(message="Venta anulada.")
