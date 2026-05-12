"""Schemas for user endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# Validación mínima de password: 6+ chars, no solo espacios.
PASSWORD_MIN = 6


def _validate_password(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < PASSWORD_MIN:
        raise ValueError(
            f"La contraseña debe tener al menos {PASSWORD_MIN} caracteres."
        )
    return value


class UserListItem(BaseModel):
    """User row exposed to the UI (sin password_hash)."""

    id: int
    username: str
    role: str | None = None
    role_id: int | None = None
    is_active: bool
    created_at: datetime | None = None


class UserCreateRequest(BaseModel):
    """Body for creating a user."""

    username: str = Field(min_length=1, max_length=100)
    role_id: int
    password: str = Field(min_length=PASSWORD_MIN, max_length=200)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return _validate_password(value)


class UserUpdateRequest(BaseModel):
    """Body for updating a user (rename + role change)."""

    username: str = Field(min_length=1, max_length=100)
    role_id: int


class UserPasswordRequest(BaseModel):
    """Body for resetting a user's password."""

    password: str = Field(min_length=PASSWORD_MIN, max_length=200)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return _validate_password(value)
