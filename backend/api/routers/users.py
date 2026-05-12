"""Users management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import CurrentUser, require_permission
from backend.api.schemas.common import CreatedResponse, MessageResponse
from backend.api.schemas.users import (
    UserCreateRequest,
    UserListItem,
    UserPasswordRequest,
    UserUpdateRequest,
)
from backend.repositories.role_permissions_repository import (
    get_permissions_for_role,
)
from backend.repositories.roles_repository import get_role_by_id
from backend.repositories.users_repository import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_name,
    toggle_user,
    update_user,
    update_user_password,
)
from backend.services.access_service import count_settings_admins
from backend.utils.security import hash_password


_LAST_ADMIN_USER_DETAIL = (
    "No podés desactivar al último administrador del lavadero."
    " Asigná el rol de administrador a otro usuario antes."
)
_LAST_ADMIN_ROLE_CHANGE_DETAIL = (
    "No podés cambiarle el rol al último administrador del lavadero."
    " Asigná el rol de administrador a otro usuario antes."
)


router = APIRouter(prefix="/users", tags=["users"])


def _ensure_user(user_id: int, lavanderia_id: int):
    user = get_user_by_id(user_id, lavanderia_id=lavanderia_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario indicado no existe en esta lavanderia.",
        )
    return user


def _ensure_role(role_id: int, lavanderia_id: int):
    role = get_role_by_id(role_id, lavanderia_id=lavanderia_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol indicado no existe en esta lavanderia.",
        )
    return role


def _block_self(target_user_id: int, current_user: CurrentUser, action: str):
    if target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No podés {action} a vos mismo.",
        )


def _serialize_listitem(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["name"],
        "role": user.get("role"),
        "role_id": user.get("role_id"),
        "is_active": bool(user.get("is_active")),
        "created_at": user.get("created_at"),
    }


@router.get("", response_model=list[UserListItem])
def list_users(
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Lista usuarios del tenant."""
    users = get_all_users(lavanderia_id=user.lavanderia_id)
    return [_serialize_listitem(u) for u in users]


@router.post("", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    body: UserCreateRequest,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Crea un usuario nuevo asignándole un rol del tenant."""
    username = body.username.strip()
    if get_user_by_name(username, lavanderia_id=user.lavanderia_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese nombre.",
        )
    _ensure_role(body.role_id, user.lavanderia_id)

    try:
        new_id = create_user(
            username,
            password_hash=hash_password(body.password),
            lavanderia_id=user.lavanderia_id,
            role_id=body.role_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"id": new_id}


@router.put("/{user_id}", response_model=MessageResponse)
def edit_user(
    user_id: int,
    body: UserUpdateRequest,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Edita username y rol. No permite editarse a uno mismo."""
    _block_self(user_id, user, "editar")
    target = _ensure_user(user_id, user.lavanderia_id)
    new_role = _ensure_role(body.role_id, user.lavanderia_id)

    new_username = body.username.strip()
    duplicate = get_user_by_name(new_username, lavanderia_id=user.lavanderia_id)
    if duplicate is not None and duplicate["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro usuario con ese nombre.",
        )

    # Guard: si cambia de rol y el target era el último admin, lo bloqueamos.
    if target.get("is_active") and target.get("role_id") != body.role_id:
        new_role_perms = get_permissions_for_role(
            new_role["id"], lavanderia_id=user.lavanderia_id
        )
        new_role_has_settings = "settings" in new_role_perms and new_role["is_active"]
        if not new_role_has_settings:
            remaining = count_settings_admins(
                user.lavanderia_id,
                exclude_user_id=user_id,
            )
            if remaining == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_LAST_ADMIN_ROLE_CHANGE_DETAIL,
                )

    try:
        update_user(
            user_id,
            new_username,
            lavanderia_id=user.lavanderia_id,
            role_id=body.role_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Usuario actualizado."}


@router.patch("/{user_id}/status", response_model=MessageResponse)
def toggle_user_status(
    user_id: int,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Activa o desactiva un usuario. No permite hacerlo sobre uno mismo."""
    _block_self(user_id, user, "deshabilitar")
    target = _ensure_user(user_id, user.lavanderia_id)

    # Guard: si está activo y se está por desactivar, simulamos el resultado.
    if target.get("is_active"):
        remaining = count_settings_admins(
            user.lavanderia_id,
            exclude_user_id=user_id,
        )
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_LAST_ADMIN_USER_DETAIL,
            )

    try:
        toggle_user(user_id, lavanderia_id=user.lavanderia_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Usuario actualizado."}


@router.patch("/{user_id}/password", response_model=MessageResponse)
def reset_user_password(
    user_id: int,
    body: UserPasswordRequest,
    user: CurrentUser = Depends(require_permission("settings")),
):
    """Resetea la contraseña de OTRO usuario. No permite cambiar la propia acá."""
    _block_self(user_id, user, "cambiar tu propia contraseña desde acá. Pediselo a otro admin")
    _ensure_user(user_id, user.lavanderia_id)
    try:
        update_user_password(
            user_id,
            hash_password(body.password),
            lavanderia_id=user.lavanderia_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Contraseña actualizada."}
