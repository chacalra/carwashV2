"""Schemas for vehicle endpoints."""

from datetime import datetime

from pydantic import BaseModel


class VehicleCreateRequest(BaseModel):
    """Create or update vehicle request."""

    license_plate: str
    vehicle_type_id: int
    owner_name: str | None = None
    phone: str | None = None


class VehicleUpdateRequest(BaseModel):
    """Edit vehicle data request."""

    vehicle_type_id: int
    owner_name: str | None = None
    phone: str | None = None


class VehicleStatusRequest(BaseModel):
    """Activate or deactivate a vehicle."""

    active: bool


class VehicleResponse(BaseModel):
    """Vehicle response."""

    id: int
    license_plate: str | None = None
    vehicle_type_id: int
    vehicle_type_name: str | None = None
    owner_name: str | None = None
    phone: str | None = None
    client_id: int | None = None
    is_active: bool
    created_at: datetime | None = None
    lavanderia_id: int
