"""Client endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.deps import CurrentUser, require_any_permission, require_permission
from backend.api.routers._errors import raise_service_error
from backend.api.schemas.clients import ClientRequest, ClientResponse
from backend.api.schemas.common import CreatedResponse
from backend.services.client_service import (
    edit_client,
    find_client_by_ruc_ci,
    get_client,
    get_clients,
    register_client,
    toggle_client_status,
)


router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientResponse])
def list_all_clients(
    only_active: bool = Query(default=False),
    current_user: CurrentUser = Depends(
        require_any_permission(
            "register_sale",
            "edit_sale",
            "manage_sales",
            "movements",
            "export",
            "settings",
        )
    ),
):
    """Lists clients for the authenticated tenant."""
    return get_clients(current_user.lavanderia_id, only_active=only_active)


@router.get("/by-ruc-ci/{ruc_ci}", response_model=ClientResponse | None)
def get_client_by_document(
    ruc_ci: str,
    current_user: CurrentUser = Depends(
        require_any_permission(
            "register_sale",
            "edit_sale",
            "manage_sales",
            "movements",
            "export",
            "settings",
        )
    ),
):
    """Finds a client by RUC/CI inside the authenticated tenant."""
    return find_client_by_ruc_ci(current_user.lavanderia_id, ruc_ci)


@router.post("", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> CreatedResponse:
    """Creates a client in the authenticated tenant."""
    try:
        client_id = register_client(
            current_user.lavanderia_id,
            payload.name,
            payload.client_type,
            ruc_ci=payload.ruc_ci,
            telefono=payload.phone,
            email=payload.email,
        )
    except ValueError as exc:
        raise_service_error(exc)

    return CreatedResponse(id=client_id)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    payload: ClientRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> ClientResponse:
    """Updates a client and returns the fresh document."""
    try:
        updated_client_id = edit_client(
            current_user.lavanderia_id,
            client_id,
            payload.name,
            payload.client_type,
            ruc_ci=payload.ruc_ci,
            telefono=payload.phone,
            email=payload.email,
        )
    except ValueError as exc:
        raise_service_error(exc)

    client = get_client(current_user.lavanderia_id, updated_client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente indicado no existe en esta lavanderia.",
        )
    return client


@router.patch("/{client_id}/status", response_model=ClientResponse)
def toggle_client(
    client_id: int,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> ClientResponse:
    """Toggles a client active status and returns the fresh document."""
    try:
        updated_client_id = toggle_client_status(current_user.lavanderia_id, client_id)
    except ValueError as exc:
        raise_service_error(exc)

    client = get_client(current_user.lavanderia_id, updated_client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente indicado no existe en esta lavanderia.",
        )
    return client
