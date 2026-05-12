"""Health endpoints."""

from backend.api.schemas.health import HealthResponse
from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Returns a lightweight health status for the API."""
    return HealthResponse(status="ok")
