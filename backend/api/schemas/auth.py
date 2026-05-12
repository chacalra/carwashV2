"""Schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    subdominio: str | None = None


class UserResponse(BaseModel):
    """Authenticated user data exposed by the API."""

    id: int
    username: str
    role: str | None = None
    lavanderia_id: int
    lavanderia_name: str | None = None


class TenantResponse(BaseModel):
    """Branding/identity of the lavanderia (tenant)."""

    id: int
    name: str
    subdominio: str | None = None
    logo_url: str | None = None
    logo_url_dark: str | None = None
    color_primario: str | None = None
    color_secundario: str | None = None
    mostrar_marca_mukusoft: bool = True


class LoginResponse(BaseModel):
    """Successful login response."""

    user: UserResponse
    tenant: TenantResponse
    permissions: list[str]
    access_token: str
    token_type: str
    expires_at: datetime
