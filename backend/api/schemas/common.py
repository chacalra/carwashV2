"""Shared API schemas."""

from pydantic import BaseModel


class CreatedResponse(BaseModel):
    """Generic create response."""

    id: int


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
