"""Carga inicial de datos base para la V2."""

from sqlalchemy import select

from database.connection import SessionLocal
from database.schema import (
    Cliente,
    Lavanderia,
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
)
from utils.security import hash_password


DEFAULT_PERMISSIONS = {
    "dashboard": "Acceso al dashboard",
    "register_income": "Registrar ventas o ingresos",
    "edit_income": "Editar ventas o ingresos",
    "void_income": "Gestionar o anular ventas o ingresos",
    "register_expense": "Registrar egresos",
    "movements": "Ver movimientos",
    "export": "Exportar datos",
    "settings": "Administrar configuración",
}

DEFAULT_TENANT = {
    "nombre_local": "Lavanderia Demo",
    "nombre_responsable": "Administrador",
    "email": "demo@carwash.local",
    "telefono": "000000000",
}

DEFAULT_ADMIN_ROLE_NAME = "admin"
DEFAULT_ADMIN_USER = {
    "nombre_usuario": "admin",
    "password": "admin123",
}

DEFAULT_GENERIC_CLIENT = {
    "nombre": "Consumidor Final",
    "tipo_cliente": "generico",
}


def seed_permissions(session):
    """Inserta el catálogo global de permisos si todavía no existe."""
    for codigo, descripcion in DEFAULT_PERMISSIONS.items():
        existing = session.scalar(
            select(Permiso).where(Permiso.codigo == codigo)
        )
        if existing is None:
            session.add(
                Permiso(
                    codigo=codigo,
                    descripcion=descripcion,
                    estado=True,
                )
            )

    session.flush()


def seed_default_lavanderia(session):
    """Crea una lavandería base de desarrollo si todavía no existe."""
    existing = session.scalar(
        select(Lavanderia).where(
            Lavanderia.nombre_local == DEFAULT_TENANT["nombre_local"]
        )
    )
    if existing is not None:
        return existing

    lavanderia = Lavanderia(
        nombre_local=DEFAULT_TENANT["nombre_local"],
        nombre_responsable=DEFAULT_TENANT["nombre_responsable"],
        email=DEFAULT_TENANT["email"],
        telefono=DEFAULT_TENANT["telefono"],
        estado=True,
    )
    session.add(lavanderia)
    session.flush()
    return lavanderia


def seed_admin_role(session, lavanderia):
    """Crea el rol administrador por defecto para la lavandería demo."""
    existing = session.scalar(
        select(Rol).where(
            Rol.lavanderia_id == lavanderia.id,
            Rol.nombre == DEFAULT_ADMIN_ROLE_NAME,
        )
    )
    if existing is not None:
        return existing

    role = Rol(
        nombre=DEFAULT_ADMIN_ROLE_NAME,
        estado=True,
        lavanderia_id=lavanderia.id,
    )
    session.add(role)
    session.flush()
    return role


def seed_admin_role_permissions(session, role):
    """Asigna todos los permisos globales al rol admin por defecto."""
    permissions = session.scalars(select(Permiso)).all()

    for permission in permissions:
        existing = session.scalar(
            select(RolPermiso).where(
                RolPermiso.rol_id == role.id,
                RolPermiso.permiso_id == permission.id,
            )
        )
        if existing is None:
            session.add(
                RolPermiso(
                    rol_id=role.id,
                    permiso_id=permission.id,
                )
            )

    session.flush()


def seed_admin_user(session, lavanderia, role):
    """Crea un usuario administrador inicial si no existe."""
    existing = session.scalar(
        select(Usuario).where(
            Usuario.lavanderia_id == lavanderia.id,
            Usuario.nombre_usuario == DEFAULT_ADMIN_USER["nombre_usuario"],
        )
    )
    if existing is not None:
        return existing

    user = Usuario(
        nombre_usuario=DEFAULT_ADMIN_USER["nombre_usuario"],
        password_hash=hash_password(DEFAULT_ADMIN_USER["password"]),
        estado=True,
        lavanderia_id=lavanderia.id,
        rol_id=role.id,
    )
    session.add(user)
    session.flush()
    return user


def seed_generic_client(session, lavanderia):
    """Crea el cliente genérico de mostrador para ventas rápidas."""
    existing = session.scalar(
        select(Cliente).where(
            Cliente.lavanderia_id == lavanderia.id,
            Cliente.tipo_cliente == DEFAULT_GENERIC_CLIENT["tipo_cliente"],
            Cliente.nombre == DEFAULT_GENERIC_CLIENT["nombre"],
        )
    )
    if existing is not None:
        return existing

    client = Cliente(
        nombre=DEFAULT_GENERIC_CLIENT["nombre"],
        tipo_cliente=DEFAULT_GENERIC_CLIENT["tipo_cliente"],
        ruc_ci=None,
        telefono=None,
        email=None,
        estado=True,
        lavanderia_id=lavanderia.id,
    )
    session.add(client)
    session.flush()
    return client


def seed_initial_data():
    """Ejecuta la carga inicial de datos base de la V2."""
    with SessionLocal() as session:
        seed_permissions(session)
        lavanderia = seed_default_lavanderia(session)
        admin_role = seed_admin_role(session, lavanderia)
        seed_admin_role_permissions(session, admin_role)
        seed_admin_user(session, lavanderia, admin_role)
        seed_generic_client(session, lavanderia)
        session.commit()
