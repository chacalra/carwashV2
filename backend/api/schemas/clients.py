"""Schemas for client endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ClientRequest(BaseModel):
    """Create or update client payload."""

    name: str = Field(min_length=1)
    client_type: str = Field(min_length=1)
    ruc_ci: str | None = None
    phone: str | None = None
    email: str | None = None


class ClientResponse(BaseModel):
    """Client response payload."""

    id: int
    name: str
    client_type: str
    ruc_ci: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool
    created_at: datetime | None = None
    lavanderia_id: int
