"""Shared FastAPI dependencies."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.repositories.users_repository import get_user_by_id
from backend.services.tenant_service import get_tenant_by_host
from backend.utils.security import TokenError, decode_access_token

DbSession = Annotated[Session, Depends(get_db)]


bearer_scheme = HTTPBearer(auto_error=False)
LOCAL_HOSTS = {"127.0.0.1", "localhost", "testserver"}


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated API user resolved from the bearer token."""

    id: int
    username: str
    role: str | None
    lavanderia_id: int
    lavanderia_name: str | None
    permissions: tuple[str, ...]


def _host_requires_tenant_validation(host: str | None) -> bool:
    """Returns whether the incoming host should be mapped to a tenant."""
    if not host:
        return False

    normalized = host.strip().lower()
    if not normalized:
        return False

    hostname = normalized.split(":", 1)[0]
    return hostname not in LOCAL_HOSTS


def _unauthorized(detail: str) -> HTTPException:
    """Builds a 401 error with the Bearer auth challenge."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_request_host(host: str | None = Header(default=None)) -> str | None:
    """Returns the request host header, if present."""
    return host


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    host: str | None = Depends(get_request_host),
) -> CurrentUser:
    """Validates the bearer token and returns the authenticated user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Hace falta un token Bearer.")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise _unauthorized(str(exc)) from exc

    lavanderia_id = payload["lavanderia_id"]

    if _host_requires_tenant_validation(host):
        try:
            host_tenant_id = get_tenant_by_host(host).id
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        if host_tenant_id != lavanderia_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El token no pertenece al tenant del host.",
            )

    user = get_user_by_id(payload["user_id"], lavanderia_id=lavanderia_id)
    if user is None or not user["is_active"]:
        raise _unauthorized("El usuario del token ya no esta disponible.")

    return CurrentUser(
        id=user["id"],
        username=user["name"],
        role=user["role"],
        lavanderia_id=user["lavanderia_id"],
        lavanderia_name=user.get("lavanderia_name"),
        permissions=tuple(payload["permissions"]),
    )


def get_lavanderia_id(current_user: CurrentUser = Depends(get_current_user)) -> int:
    """Returns the tenant id bound to the authenticated user."""
    return current_user.lavanderia_id


def require_permission(permission: str) -> Callable[[CurrentUser], CurrentUser]:
    """Builds a dependency that requires a single permission."""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para esta accion.",
            )
        return current_user

    return dependency


def require_any_permission(*permissions: str) -> Callable[[CurrentUser], CurrentUser]:
    """Builds a dependency that accepts any one of the provided permissions."""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(permission in current_user.permissions for permission in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para esta accion.",
            )
        return current_user

    return dependency
