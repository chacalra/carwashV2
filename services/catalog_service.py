"""Reglas de negocio para gestion de catalogos (servicios, categorias, tipos vehiculo, roles, usuarios)."""

import sqlite3

from repositories.expense_categories_repository import (
    create_category,
    delete_category,
    is_category_in_use,
    toggle_category,
    update_category_name,
)
from repositories.role_permissions_repository import set_permissions_for_role
from repositories.roles_repository import create_role, toggle_role
from repositories.products_repository import (
    create_product,
    delete_product,
    is_product_in_use,
    toggle_product,
    update_product_name,
)
from repositories.services_repository import (
    create_service,
    delete_service,
    is_service_in_use,
    toggle_service,
    update_service_name,
)
from repositories.users_repository import (
    create_user,
    toggle_user,
    update_user,
    update_user_password,
)
from repositories.vehicle_types_repository import (
    create_vehicle_type,
    delete_vehicle_type,
    is_vehicle_type_in_use,
    toggle_vehicle_type,
    update_vehicle_type_name,
)
from utils.security import hash_password


def _validate_name(name):
    """Valida que el nombre no este vacio."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("El nombre no puede estar vacio.")
    return name.strip()


def _validate_password(password):
    """Valida que la contrasena tenga al menos 4 caracteres."""
    if not isinstance(password, str) or len(password.strip()) < 4:
        raise ValueError("La contrasena debe tener al menos 4 caracteres.")
    return password.strip()


# --- Servicios ---


def add_service(name):
    """Valida y crea un nuevo servicio. Devuelve su id."""
    clean = _validate_name(name)
    try:
        return create_service(clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un servicio con el nombre '{clean}'.")


def rename_service(service_id, name):
    """Valida y actualiza el nombre de un servicio."""
    clean = _validate_name(name)
    try:
        update_service_name(service_id, clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un servicio con el nombre '{clean}'.")


def toggle_service_status(service_id):
    """Activa o desactiva un servicio."""
    toggle_service(service_id)


def remove_service(service_id):
    """Elimina un servicio si no esta siendo usado por ningun ingreso."""
    if is_service_in_use(service_id):
        raise ValueError("No se puede eliminar: este servicio tiene ingresos registrados.")
    delete_service(service_id)


# --- Productos ---


def add_product(name):
    """Valida y crea un nuevo producto. Devuelve su id."""
    clean = _validate_name(name)
    try:
        return create_product(clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un producto con el nombre '{clean}'.")


def rename_product(product_id, name):
    """Valida y actualiza el nombre de un producto."""
    clean = _validate_name(name)
    try:
        update_product_name(product_id, clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un producto con el nombre '{clean}'.")


def toggle_product_status(product_id):
    """Activa o desactiva un producto."""
    toggle_product(product_id)


def remove_product(product_id):
    """Elimina un producto si no esta siendo usado por ningun ingreso."""
    if is_product_in_use(product_id):
        raise ValueError("No se puede eliminar: este producto tiene ingresos registrados.")
    delete_product(product_id)


# --- Categorias de egreso ---


def add_category(name):
    """Valida y crea una nueva categoria. Devuelve su id."""
    clean = _validate_name(name)
    try:
        return create_category(clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe una categoria con el nombre '{clean}'.")


def rename_category(category_id, name):
    """Valida y actualiza el nombre de una categoria."""
    clean = _validate_name(name)
    try:
        update_category_name(category_id, clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe una categoria con el nombre '{clean}'.")


def toggle_category_status(category_id):
    """Activa o desactiva una categoria."""
    toggle_category(category_id)


def remove_category(category_id):
    """Elimina una categoria si no esta siendo usada por ningun egreso."""
    if is_category_in_use(category_id):
        raise ValueError("No se puede eliminar: esta categoria tiene egresos registrados.")
    delete_category(category_id)


# --- Tipos de vehiculo ---


def add_vehicle_type(name):
    """Valida y crea un nuevo tipo de vehiculo. Devuelve su id."""
    clean = _validate_name(name)
    try:
        return create_vehicle_type(clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un tipo de vehiculo con el nombre '{clean}'.")


def rename_vehicle_type(vehicle_type_id, name):
    """Valida y actualiza el nombre de un tipo de vehiculo."""
    clean = _validate_name(name)
    try:
        update_vehicle_type_name(vehicle_type_id, clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un tipo de vehiculo con el nombre '{clean}'.")


def toggle_vehicle_type_status(vehicle_type_id):
    """Activa o desactiva un tipo de vehiculo."""
    toggle_vehicle_type(vehicle_type_id)


def remove_vehicle_type(vehicle_type_id):
    """Elimina un tipo de vehiculo si no esta siendo usado por ningun vehiculo."""
    if is_vehicle_type_in_use(vehicle_type_id):
        raise ValueError("No se puede eliminar: este tipo tiene vehiculos registrados.")
    delete_vehicle_type(vehicle_type_id)


# --- Roles ---


def add_role(name):
    """Valida y crea un nuevo rol. Devuelve su id."""
    clean = _validate_name(name)
    try:
        return create_role(clean)
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un rol con el nombre '{clean}'.")


def toggle_role_status(role_id):
    """Activa o desactiva un rol."""
    toggle_role(role_id)


def save_role_permissions(role_name, permissions):
    """Guarda los permisos de un rol, reemplazando los anteriores."""
    set_permissions_for_role(role_name, permissions)


# --- Usuarios ---


def add_user(name, role, password):
    """Valida y crea un nuevo usuario con contrasena. Devuelve su id."""
    clean_name = _validate_name(name)
    clean_password = _validate_password(password)
    if not role or not role.strip():
        raise ValueError("El rol es obligatorio.")
    return create_user(clean_name, role.strip(), hash_password(clean_password))


def edit_user(user_id, name, role):
    """Valida y actualiza nombre y rol de un usuario."""
    clean_name = _validate_name(name)
    if not role or not role.strip():
        raise ValueError("El rol es obligatorio.")
    update_user(user_id, clean_name, role.strip())


def change_user_password(user_id, password):
    """Valida y actualiza la contrasena de un usuario."""
    clean = _validate_password(password)
    update_user_password(user_id, hash_password(clean))


def toggle_user_status(user_id):
    """Activa o desactiva un usuario."""
    toggle_user(user_id)
