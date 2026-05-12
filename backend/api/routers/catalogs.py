"""Catalog endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.deps import CurrentUser, require_any_permission, require_permission
from backend.api.routers._errors import raise_service_error
from backend.api.schemas.catalogs import (
    CatalogItem,
    CatalogMutationRequest,
    CatalogStatusResponse,
    ExpenseCategoryItem,
    VehicleTypeItem,
)
from backend.api.schemas.common import CreatedResponse, MessageResponse
from backend.repositories.expense_categories_repository import (
    get_active_categories,
    get_all_categories,
    get_category_by_id,
)
from backend.repositories.products_repository import (
    get_active_products,
    get_all_products,
    get_product_by_id,
)
from backend.repositories.services_repository import (
    get_active_services,
    get_all_services,
    get_service_by_id,
)
from backend.repositories.vehicle_types_repository import (
    get_active_vehicle_types,
    get_all_vehicle_types,
    get_vehicle_type_by_id,
)
from backend.services.catalog_service import (
    add_category,
    add_product,
    add_service,
    add_vehicle_type,
    remove_category,
    remove_product,
    remove_service,
    remove_vehicle_type,
    rename_category,
    rename_product,
    rename_service,
    rename_vehicle_type,
    toggle_category_status,
    toggle_product_status,
    toggle_service_status,
    toggle_vehicle_type_status,
)


router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _catalog_read_permission():
    """Shared read access for operational catalog usage."""
    return require_any_permission(
        "register_sale",
        "edit_sale",
        "manage_sales",
        "register_expense",
        "movements",
        "export",
        "settings",
    )


def _catalog_item(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "price": float(row["price"]) if row.get("price") is not None else None,
        "is_active": bool(row["is_active"]),
        "created_at": row.get("created_at"),
        "lavanderia_id": row["lavanderia_id"],
    }


def _simple_item(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "is_active": bool(row["is_active"]),
        "created_at": row.get("created_at"),
        "lavanderia_id": row["lavanderia_id"],
    }


# --- services ---

@router.get("/services", response_model=list[CatalogItem])
def list_services(
    only_active: bool = Query(default=True),
    current_user: CurrentUser = Depends(_catalog_read_permission()),
):
    """Lists services for a tenant."""
    rows = (
        get_active_services(lavanderia_id=current_user.lavanderia_id)
        if only_active
        else get_all_services(lavanderia_id=current_user.lavanderia_id)
    )
    return [_catalog_item(row) for row in rows]


@router.post("/services", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_service_item(
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CreatedResponse:
    """Creates a service catalog item."""
    try:
        created_id = add_service(
            payload.name,
            lavanderia_id=current_user.lavanderia_id,
            price=payload.price or 0,
        )
    except ValueError as exc:
        raise_service_error(exc)
    return CreatedResponse(id=created_id)


@router.put("/services/{service_id}", response_model=CatalogItem)
def update_service_item(
    service_id: int,
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CatalogItem:
    """Updates a service catalog item."""
    try:
        rename_service(
            service_id,
            payload.name,
            lavanderia_id=current_user.lavanderia_id,
            price=payload.price,
        )
    except ValueError as exc:
        raise_service_error(exc)

    item = get_service_by_id(service_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El servicio indicado no existe.")
    return _catalog_item(item)


@router.patch("/services/{service_id}/status", response_model=CatalogStatusResponse)
def toggle_service_item(
    service_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CatalogStatusResponse:
    """Toggles a service catalog item."""
    try:
        toggle_service_status(service_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    item = get_service_by_id(service_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El servicio indicado no existe.")
    return CatalogStatusResponse(id=service_id, is_active=bool(item["is_active"]))


@router.delete("/services/{service_id}", response_model=MessageResponse)
def delete_service_item(
    service_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> MessageResponse:
    """Deletes a service catalog item."""
    try:
        remove_service(service_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)
    return MessageResponse(message="Servicio eliminado.")


# --- products ---

@router.get("/products", response_model=list[CatalogItem])
def list_products(
    only_active: bool = Query(default=True),
    current_user: CurrentUser = Depends(_catalog_read_permission()),
):
    """Lists products for a tenant."""
    rows = (
        get_active_products(lavanderia_id=current_user.lavanderia_id)
        if only_active
        else get_all_products(lavanderia_id=current_user.lavanderia_id)
    )
    return [_catalog_item(row) for row in rows]


@router.post("/products", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_product_item(
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CreatedResponse:
    """Creates a product catalog item."""
    try:
        created_id = add_product(
            payload.name,
            lavanderia_id=current_user.lavanderia_id,
            price=payload.price or 0,
        )
    except ValueError as exc:
        raise_service_error(exc)
    return CreatedResponse(id=created_id)


@router.put("/products/{product_id}", response_model=CatalogItem)
def update_product_item(
    product_id: int,
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CatalogItem:
    """Updates a product catalog item."""
    try:
        rename_product(
            product_id,
            payload.name,
            lavanderia_id=current_user.lavanderia_id,
            price=payload.price,
        )
    except ValueError as exc:
        raise_service_error(exc)

    item = get_product_by_id(product_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El producto indicado no existe.")
    return _catalog_item(item)


@router.patch("/products/{product_id}/status", response_model=CatalogStatusResponse)
def toggle_product_item(
    product_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CatalogStatusResponse:
    """Toggles a product catalog item."""
    try:
        toggle_product_status(product_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    item = get_product_by_id(product_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El producto indicado no existe.")
    return CatalogStatusResponse(id=product_id, is_active=bool(item["is_active"]))


@router.delete("/products/{product_id}", response_model=MessageResponse)
def delete_product_item(
    product_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> MessageResponse:
    """Deletes a product catalog item."""
    try:
        remove_product(product_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)
    return MessageResponse(message="Producto eliminado.")


# --- expense categories ---

@router.get("/expense-categories", response_model=list[ExpenseCategoryItem])
def list_expense_categories(
    only_active: bool = Query(default=True),
    current_user: CurrentUser = Depends(_catalog_read_permission()),
):
    """Lists expense categories for a tenant."""
    rows = (
        get_active_categories(lavanderia_id=current_user.lavanderia_id)
        if only_active
        else get_all_categories(lavanderia_id=current_user.lavanderia_id)
    )
    return [_simple_item(row) for row in rows]


@router.post("/expense-categories", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_expense_category(
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CreatedResponse:
    """Creates an expense category."""
    try:
        created_id = add_category(payload.name, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)
    return CreatedResponse(id=created_id)


@router.put("/expense-categories/{category_id}", response_model=ExpenseCategoryItem)
def update_expense_category(
    category_id: int,
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> ExpenseCategoryItem:
    """Updates an expense category."""
    try:
        rename_category(category_id, payload.name, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    item = get_category_by_id(category_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La categoria indicada no existe.")
    return _simple_item(item)


@router.patch("/expense-categories/{category_id}/status", response_model=CatalogStatusResponse)
def toggle_expense_category(
    category_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CatalogStatusResponse:
    """Toggles an expense category."""
    try:
        toggle_category_status(category_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    item = get_category_by_id(category_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La categoria indicada no existe.")
    return CatalogStatusResponse(id=category_id, is_active=bool(item["is_active"]))


@router.delete("/expense-categories/{category_id}", response_model=MessageResponse)
def delete_expense_category(
    category_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> MessageResponse:
    """Deletes an expense category."""
    try:
        remove_category(category_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)
    return MessageResponse(message="Categoria eliminada.")


# --- vehicle types ---

@router.get("/vehicle-types", response_model=list[VehicleTypeItem])
def list_vehicle_types(
    only_active: bool = Query(default=True),
    current_user: CurrentUser = Depends(_catalog_read_permission()),
):
    """Lists vehicle types for a tenant."""
    rows = (
        get_active_vehicle_types(lavanderia_id=current_user.lavanderia_id)
        if only_active
        else get_all_vehicle_types(lavanderia_id=current_user.lavanderia_id)
    )
    return [_simple_item(row) for row in rows]


@router.post("/vehicle-types", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle_type_item(
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CreatedResponse:
    """Creates a vehicle type."""
    try:
        created_id = add_vehicle_type(payload.name, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)
    return CreatedResponse(id=created_id)


@router.put("/vehicle-types/{vehicle_type_id}", response_model=VehicleTypeItem)
def update_vehicle_type_item(
    vehicle_type_id: int,
    payload: CatalogMutationRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> VehicleTypeItem:
    """Updates a vehicle type."""
    try:
        rename_vehicle_type(vehicle_type_id, payload.name, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    item = get_vehicle_type_by_id(vehicle_type_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El tipo de vehiculo indicado no existe.")
    return _simple_item(item)


@router.patch("/vehicle-types/{vehicle_type_id}/status", response_model=CatalogStatusResponse)
def toggle_vehicle_type_item(
    vehicle_type_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CatalogStatusResponse:
    """Toggles a vehicle type."""
    try:
        toggle_vehicle_type_status(vehicle_type_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)

    item = get_vehicle_type_by_id(vehicle_type_id, lavanderia_id=current_user.lavanderia_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El tipo de vehiculo indicado no existe.")
    return CatalogStatusResponse(id=vehicle_type_id, is_active=bool(item["is_active"]))


@router.delete("/vehicle-types/{vehicle_type_id}", response_model=MessageResponse)
def delete_vehicle_type_item(
    vehicle_type_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> MessageResponse:
    """Deletes a vehicle type."""
    try:
        remove_vehicle_type(vehicle_type_id, lavanderia_id=current_user.lavanderia_id)
    except ValueError as exc:
        raise_service_error(exc)
    return MessageResponse(message="Tipo de vehiculo eliminado.")
