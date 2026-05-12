"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_request_host
from backend.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TenantResponse,
    UserResponse,
)
from backend.services.auth_service import login as authenticate_user
from backend.utils.security import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


def _status_for_auth_error(message: str) -> int:
    """Maps service-level auth errors to HTTP status codes."""
    if "incorrectos" in message:
        return status.HTTP_401_UNAUTHORIZED
    return status.HTTP_400_BAD_REQUEST


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, host: str | None = Depends(get_request_host)) -> LoginResponse:
    """Authenticates a user inside the tenant resolved from subdomain or Host."""
    try:
        user, permissions = authenticate_user(
            payload.username,
            payload.password,
            subdominio=payload.subdominio,
            host=None if payload.subdominio else host,
        )
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(
            status_code=_status_for_auth_error(message),
            detail=message,
        ) from exc

    access_token, expires_at = create_access_token(
        user_id=user["id"],
        lavanderia_id=user["lavanderia_id"],
        permissions=permissions,
    )

    tenant_data = user.get("tenant") or {
        "id": user["lavanderia_id"],
        "name": user.get("lavanderia_name") or "",
    }

    return LoginResponse(
        user=UserResponse(
            id=user["id"],
            username=user["name"],
            role=user["role"],
            lavanderia_id=user["lavanderia_id"],
            lavanderia_name=user.get("lavanderia_name"),
        ),
        tenant=TenantResponse(**tenant_data),
        permissions=permissions,
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
    )
