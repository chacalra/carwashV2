"""Reglas transversales de control de acceso para el tenant.

`count_settings_admins` cuenta usuarios activos del tenant que pueden
administrar (i.e. tienen un rol activo con el permiso `settings`).

Cualquier router que pueda dejar al tenant sin admin debería simular el
cambio antes de commitearlo y abortar si el resultado dejaría el contador
en 0.
"""

from sqlalchemy import distinct, func, select

from backend.database.connection import SessionLocal
from backend.database.schema import Permiso, Rol, RolPermiso, Usuario


SETTINGS_PERMISSION = "settings"


def count_settings_admins(
    lavanderia_id,
    *,
    exclude_user_id=None,
    excluded_role_ids=None,
    role_settings_overrides=None,
):
    """Cuenta admins efectivos del tenant.

    Un "admin efectivo" = usuario activo cuyo rol activo tiene `settings`.

    Parámetros para simular cambios en curso:

    - `exclude_user_id`: el id de un usuario que se está por desactivar
      (lo descontamos del cuenteo).
    - `excluded_role_ids`: roles que se están por desactivar — usuarios cuyo
      rol esté en este set no cuentan como admins.
    - `role_settings_overrides`: dict {role_id: bool} — sobreescribe si un
      rol tiene `settings`. Útil al cambiar permisos del rol antes de commit.
      Roles ausentes del dict se evalúan contra la tabla actual.
    """
    excluded_role_ids = set(excluded_role_ids or ())
    role_settings_overrides = role_settings_overrides or {}

    with SessionLocal() as session:
        # Roles activos del tenant que tienen `settings` según la DB hoy.
        query = (
            select(distinct(Rol.id))
            .join(RolPermiso, RolPermiso.rol_id == Rol.id)
            .join(Permiso, Permiso.id == RolPermiso.permiso_id)
            .where(
                Rol.lavanderia_id == lavanderia_id,
                Rol.estado.is_(True),
                Permiso.codigo == SETTINGS_PERMISSION,
            )
        )
        roles_with_settings_db = set(session.scalars(query).all())

        # Aplicamos los overrides (representan el estado *post-cambio*).
        roles_with_settings = set(roles_with_settings_db)
        for role_id, has_settings in role_settings_overrides.items():
            if has_settings:
                roles_with_settings.add(role_id)
            else:
                roles_with_settings.discard(role_id)

        # Quitamos roles que se están por desactivar.
        roles_with_settings -= excluded_role_ids

        if not roles_with_settings:
            return 0

        # Contamos usuarios activos cuyo rol está en ese set.
        user_query = (
            select(func.count(Usuario.id))
            .where(
                Usuario.lavanderia_id == lavanderia_id,
                Usuario.estado.is_(True),
                Usuario.rol_id.in_(roles_with_settings),
            )
        )
        if exclude_user_id is not None:
            user_query = user_query.where(Usuario.id != exclude_user_id)
        return int(session.scalar(user_query) or 0)
