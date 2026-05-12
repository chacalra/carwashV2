"""Roles + permissions endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import CurrentUser, require_permission
from backend.api.schemas.common import CreatedResponse, MessageResponse
from backend.api.schemas.roles import (
    RoleCreateRequest,
    RolePermissionsRequest,
    RoleRenameRequest,
    RoleResponse,
)
from backend.repositories.role_permissions_repository import (
    get_permissions_for_role,
    set_permissions_for_role,
)
from backend.repositories.roles_repository import (
    create_role,
    get_all_roles,
    get_permission_counts,
    get_role_by_id,
    get_role_by_name,
    rename_role,
    toggle_role,
)
from backend.services.access_service import count_settings_admins


router = APIRouter(prefix="/roles", tags=["roles"])


_LAST_ADMIN_ROLE_DETAIL = (
    "No podés desactivar este rol: dejaría al lavadero sin administradores activos."
    " Asigná el rol de administrador a otro usuario antes."
)
_LAST_ADMIN_PERMS_DETAIL = (
    "No podés sacarle este permiso al rol: dejaría al lavadero sin administradores activos."
    " Asigná el rol de administrador a otro usuario antes."
)


def _ensure_role(role_id: int, lavanderia_id: int):
    """Devuelve el rol o lanza 404 si no existe en el tenant."""
    role = get_role_by_id(role_id, lavanderia_id=lavanderia_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El rol indicado no existe en esta lavanderia.",
        )
    return role


@router.get("", response_model=list[RoleResponse])
def list_roles(
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Lista los roles del tenant con cuenta de permisos asignados."""
    roles = get_all_roles(lavanderia_id=user.lavanderia_id)
    counts = get_permission_counts(lavanderia_id=user.lavanderia_id)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "is_active": bool(r["is_active"]),
            "permission_count": int(counts.get(r["id"], 0)),
        }
        for r in roles
    ]


@router.post("", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_new_role(
    body: RoleCreateRequest,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Crea un rol nuevo con cero permisos."""
    name = body.name.strip()
    existing = get_role_by_name(name, lavanderia_id=user.lavanderia_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un rol con ese nombre en la lavanderia.",
        )
    try:
        role_id = create_role(name, lavanderia_id=user.lavanderia_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"id": role_id}


@router.put("/{role_id}", response_model=MessageResponse)
def rename_existing_role(
    role_id: int,
    body: RoleRenameRequest,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Renombra un rol existente."""
    _ensure_role(role_id, user.lavanderia_id)
    new_name = body.name.strip()

    duplicate = get_role_by_name(new_name, lavanderia_id=user.lavanderia_id)
    if duplicate is not None and duplicate["id"] != role_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro rol con ese nombre.",
        )

    try:
        rename_role(role_id, new_name, lavanderia_id=user.lavanderia_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Rol renombrado."}


@router.patch("/{role_id}/status", response_model=MessageResponse)
def toggle_role_status(
    role_id: int,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Activa o desactiva un rol. Si es el rol del propio usuario, prohíbe."""
    role = _ensure_role(role_id, user.lavanderia_id)

    if role["name"] == user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No podés desactivar tu propio rol.",
        )

    # Guard: si el rol está activo y se está por desactivar, validar que no
    # nos quedemos sin admins.
    if role["is_active"]:
        remaining = count_settings_admins(
            user.lavanderia_id,
            excluded_role_ids=[role_id],
        )
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_LAST_ADMIN_ROLE_DETAIL,
            )

    try:
        toggle_role(role_id, lavanderia_id=user.lavanderia_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Rol actualizado."}


@router.get("/{role_id}/permissions", response_model=list[str])
def list_role_permissions(
    role_id: int,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Devuelve los códigos de permiso asignados al rol."""
    _ensure_role(role_id, user.lavanderia_id)
    return get_permissions_for_role(role_id, lavanderia_id=user.lavanderia_id)


@router.put("/{role_id}/permissions", response_model=MessageResponse)
def replace_role_permissions(
    role_id: int,
    body: RolePermissionsRequest,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Reemplaza la lista de permisos del rol."""
    role = _ensure_role(role_id, user.lavanderia_id)
    new_perms = set(body.permissions)
    will_have_settings = "settings" in new_perms

    # Guard: si es el propio rol del user logueado, no puede sacarse `settings`.
    if role["name"] == user.role and not will_have_settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No podés sacarle el permiso 'settings' a tu propio rol."
                " Pedí que otro admin lo haga."
            ),
        )

    # Guard: si tras el cambio este rol perdería `settings`, asegurar que
    # quede al menos otro admin en el tenant.
    if not will_have_settings:
        remaining = count_settings_admins(
            user.lavanderia_id,
            role_settings_overrides={role_id: False},
        )
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_LAST_ADMIN_PERMS_DETAIL,
            )

    try:
        set_permissions_for_role(
            role_id,
            body.permissions,
            lavanderia_id=user.lavanderia_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Permisos actualizados."}
