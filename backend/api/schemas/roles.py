"""Schemas for role endpoints."""

from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    """Role row exposed to the UI."""

    id: int
    name: str
    is_active: bool
    permission_count: int


class RoleCreateRequest(BaseModel):
    """Body for creating a role."""

    name: str = Field(min_length=1, max_length=100)


class RoleRenameRequest(BaseModel):
    """Body for renaming a role."""

    name: str = Field(min_length=1, max_length=100)


class RolePermissionsRequest(BaseModel):
    """Body for replacing the permissions of a role."""

    permissions: list[str] = Field(default_factory=list)
