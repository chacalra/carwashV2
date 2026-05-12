"""Schemas for catalog endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    """Common catalog item shape."""

    id: int
    name: str
    price: float | None = None
    is_active: bool
    created_at: datetime | None = None
    lavanderia_id: int


class ExpenseCategoryItem(BaseModel):
    """Expense category response."""

    id: int
    name: str
    is_active: bool
    created_at: datetime | None = None
    lavanderia_id: int


class VehicleTypeItem(BaseModel):
    """Vehicle type response."""

    id: int
    name: str
    is_active: bool
    created_at: datetime | None = None
    lavanderia_id: int


class CatalogMutationRequest(BaseModel):
    """Create or update payload for catalog entries."""

    name: str = Field(min_length=1)
    price: float | None = None


class CatalogStatusResponse(BaseModel):
    """Response payload for activation toggles."""

    id: int
    is_active: bool
