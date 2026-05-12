"""Vehicle endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.deps import CurrentUser, require_any_permission, require_permission
from backend.api.routers._errors import raise_service_error
from backend.api.schemas.common import CreatedResponse
from backend.api.schemas.vehicles import (
    VehicleCreateRequest,
    VehicleResponse,
    VehicleStatusRequest,
    VehicleUpdateRequest,
)
from backend.repositories.vehicles_repository import find_vehicle_by_plate
from backend.services.vehicle_service import (
    edit_vehicle,
    find_or_create_vehicle,
    get_vehicle,
    list_vehicles,
    toggle_vehicle_status,
)


router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleResponse])
def list_vehicles_endpoint(
    only_active: bool = Query(default=True),
    search: str | None = Query(default=None),
    current_user: CurrentUser = Depends(
        require_any_permission("register_sale", "settings")
    ),
):
    """Lists vehicles for the tenant."""
    return list_vehicles(
        lavanderia_id=current_user.lavanderia_id,
        only_active=only_active,
        search=search,
    )


@router.get("/by-plate/{license_plate}", response_model=VehicleResponse | None)
def get_vehicle_by_plate(
    license_plate: str,
    current_user: CurrentUser = Depends(require_permission("register_sale")),
):
    """Finds a vehicle by plate."""
    return find_vehicle_by_plate(license_plate, lavanderia_id=current_user.lavanderia_id)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle_detail(
    vehicle_id: int,
    current_user: CurrentUser = Depends(
        require_any_permission("register_sale", "settings")
    ),
) -> VehicleResponse:
    """Returns one vehicle by id."""
    vehicle = get_vehicle(vehicle_id, lavanderia_id=current_user.lavanderia_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El vehiculo indicado no existe.",
        )
    return vehicle


@router.post("", response_model=CreatedResponse)
def create_or_update_vehicle(
    payload: VehicleCreateRequest,
    current_user: CurrentUser = Depends(require_permission("register_sale")),
) -> CreatedResponse:
    """Finds or creates a vehicle and returns its id."""
    try:
        vehicle_id = find_or_create_vehicle(
            payload.license_plate,
            payload.vehicle_type_id,
            owner_name=payload.owner_name,
            phone=payload.phone,
            lavanderia_id=current_user.lavanderia_id,
        )
    except ValueError as exc:
        raise_service_error(exc)

    return CreatedResponse(id=vehicle_id)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle_detail(
    vehicle_id: int,
    payload: VehicleUpdateRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> VehicleResponse:
    """Updates vehicle data and returns the fresh document."""
    try:
        edit_vehicle(
            vehicle_id,
            payload.vehicle_type_id,
            owner_name=payload.owner_name,
            phone=payload.phone,
            lavanderia_id=current_user.lavanderia_id,
        )
    except ValueError as exc:
        raise_service_error(exc)

    vehicle = get_vehicle(vehicle_id, lavanderia_id=current_user.lavanderia_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El vehiculo indicado no existe.",
        )
    return vehicle


@router.patch("/{vehicle_id}/status", response_model=VehicleResponse)
def set_vehicle_status_endpoint(
    vehicle_id: int,
    payload: VehicleStatusRequest,
    current_user: CurrentUser = Depends(require_permission("settings")),
) -> VehicleResponse:
    """Activates or deactivates a vehicle."""
    try:
        toggle_vehicle_status(
            vehicle_id,
            payload.active,
            lavanderia_id=current_user.lavanderia_id,
        )
    except ValueError as exc:
        raise_service_error(exc)

    vehicle = get_vehicle(vehicle_id, lavanderia_id=current_user.lavanderia_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El vehiculo indicado no existe.",
        )
    return vehicle
