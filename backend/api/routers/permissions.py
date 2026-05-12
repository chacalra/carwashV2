"""Permissions catalog endpoint.

Solo lectura. La fuente de verdad es `PERMISSIONS` en auth_service.
"""

from fastapi import APIRouter, Depends

from backend.api.deps import CurrentUser, require_permission
from backend.api.schemas.permissions import PermissionItem
from backend.services.auth_service import PERMISSIONS


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionItem])
def list_permissions(
    _user: CurrentUser = Depends(require_permission("settings")),
):
    """Returns all permissions available in the system."""
    return [{"code": code, "label": label} for code, label in PERMISSIONS.items()]
