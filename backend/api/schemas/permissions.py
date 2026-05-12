"""Schemas for permissions endpoints."""

from pydantic import BaseModel


class PermissionItem(BaseModel):
    """Single permission entry exposed to the UI."""

    code: str
    label: str
