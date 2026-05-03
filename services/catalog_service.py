"""Reglas de negocio para gestion de catalogos de la V2."""

from sqlalchemy.exc import IntegrityError

from repositories.expense_categories_repository import (
    create_category,
    delete_category,
    get_active_categories,
    is_category_in_use,
    toggle_category,
    update_category_name,
)
from repositories.role_permissions_repository import set_permissions_for_role
from repositories.roles_repository import create_role, toggle_role
from repositories.products_repository import (
    create_product,
    delete_product,
    get_active_products,
    is_product_in_use,
    toggle_product,
    update_product_name,
)
from repositories.services_repository import (
    create_service,
    delete_service,
    get_active_services,
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
    get_active_vehicle_types,
    is_vehicle_type_in_use,
    toggle_vehicle_type,
    update_vehicle_type_name,
)
from utils.security import hash_password
from utils.tenant_context import resolve_lavanderia_id


def _clear_streamlit_cache(cached_fn):
    """Limpia una cache de Streamlit si la funcion soporta clear()."""
    clear = getattr(cached_fn, "clear", None)
    if callable(clear):
        clear()


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


def _require_tenant(lavanderia_id=None):
    """Obtiene la lavanderia actual desde argumento o session_state."""
    return resolve_lavanderia_id(lavanderia_id, required=True)


# --- Servicios ---


def add_service(name, lavanderia_id=None):
    """Valida y crea un nuevo servicio. Devuelve su id."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        created_id = create_service(clean, target_lavanderia_id)
        _clear_streamlit_cache(get_active_services)
        return created_id
    except IntegrityError:
        raise ValueError(f"Ya existe un servicio con el nombre '{clean}'.")


def rename_service(service_id, name, lavanderia_id=None):
    """Valida y actualiza el nombre de un servicio."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        update_service_name(service_id, clean, lavanderia_id=target_lavanderia_id)
        _clear_streamlit_cache(get_active_services)
    except IntegrityError:
        raise ValueError(f"Ya existe un servicio con el nombre '{clean}'.")


def toggle_service_status(service_id, lavanderia_id=None):
    """Activa o desactiva un servicio."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    toggle_service(service_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_services)


def remove_service(service_id, lavanderia_id=None):
    """Elimina un servicio si no esta siendo usado por ninguna venta."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    if is_service_in_use(service_id, lavanderia_id=target_lavanderia_id):
        raise ValueError("No se puede eliminar: este servicio ya tiene ventas registradas.")
    delete_service(service_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_services)


# --- Productos ---


def add_product(name, lavanderia_id=None):
    """Valida y crea un nuevo producto. Devuelve su id."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        created_id = create_product(clean, target_lavanderia_id)
        _clear_streamlit_cache(get_active_products)
        return created_id
    except IntegrityError:
        raise ValueError(f"Ya existe un producto con el nombre '{clean}'.")


def rename_product(product_id, name, lavanderia_id=None):
    """Valida y actualiza el nombre de un producto."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        update_product_name(product_id, clean, lavanderia_id=target_lavanderia_id)
        _clear_streamlit_cache(get_active_products)
    except IntegrityError:
        raise ValueError(f"Ya existe un producto con el nombre '{clean}'.")


def toggle_product_status(product_id, lavanderia_id=None):
    """Activa o desactiva un producto."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    toggle_product(product_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_products)


def remove_product(product_id, lavanderia_id=None):
    """Elimina un producto si no esta siendo usado por ninguna venta."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    if is_product_in_use(product_id, lavanderia_id=target_lavanderia_id):
        raise ValueError("No se puede eliminar: este producto ya tiene ventas registradas.")
    delete_product(product_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_products)


# --- Categorias de egreso ---


def add_category(name, lavanderia_id=None):
    """Valida y crea una nueva categoria. Devuelve su id."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        created_id = create_category(clean, target_lavanderia_id)
        _clear_streamlit_cache(get_active_categories)
        return created_id
    except IntegrityError:
        raise ValueError(f"Ya existe una categoria con el nombre '{clean}'.")


def rename_category(category_id, name, lavanderia_id=None):
    """Valida y actualiza el nombre de una categoria."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        update_category_name(category_id, clean, lavanderia_id=target_lavanderia_id)
        _clear_streamlit_cache(get_active_categories)
    except IntegrityError:
        raise ValueError(f"Ya existe una categoria con el nombre '{clean}'.")


def toggle_category_status(category_id, lavanderia_id=None):
    """Activa o desactiva una categoria."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    toggle_category(category_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_categories)


def remove_category(category_id, lavanderia_id=None):
    """Elimina una categoria si no esta siendo usada por ningun egreso."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    if is_category_in_use(category_id, lavanderia_id=target_lavanderia_id):
        raise ValueError("No se puede eliminar: esta categoria ya tiene egresos registrados.")
    delete_category(category_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_categories)


# --- Tipos de vehiculo ---


def add_vehicle_type(name, lavanderia_id=None):
    """Valida y crea un nuevo tipo de vehiculo. Devuelve su id."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        created_id = create_vehicle_type(clean, target_lavanderia_id)
        _clear_streamlit_cache(get_active_vehicle_types)
        return created_id
    except IntegrityError:
        raise ValueError(f"Ya existe un tipo de vehiculo con el nombre '{clean}'.")


def rename_vehicle_type(vehicle_type_id, name, lavanderia_id=None):
    """Valida y actualiza el nombre de un tipo de vehiculo."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        update_vehicle_type_name(
            vehicle_type_id,
            clean,
            lavanderia_id=target_lavanderia_id,
        )
        _clear_streamlit_cache(get_active_vehicle_types)
    except IntegrityError:
        raise ValueError(f"Ya existe un tipo de vehiculo con el nombre '{clean}'.")


def toggle_vehicle_type_status(vehicle_type_id, lavanderia_id=None):
    """Activa o desactiva un tipo de vehiculo."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    toggle_vehicle_type(vehicle_type_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_vehicle_types)


def remove_vehicle_type(vehicle_type_id, lavanderia_id=None):
    """Elimina un tipo de vehiculo si no esta siendo usado por ningun vehiculo."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    if is_vehicle_type_in_use(vehicle_type_id, lavanderia_id=target_lavanderia_id):
        raise ValueError("No se puede eliminar: este tipo ya tiene vehiculos registrados.")
    delete_vehicle_type(vehicle_type_id, lavanderia_id=target_lavanderia_id)
    _clear_streamlit_cache(get_active_vehicle_types)


# --- Roles ---


def add_role(name, lavanderia_id=None):
    """Valida y crea un nuevo rol. Devuelve su id."""
    clean = _validate_name(name)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        return create_role(clean, target_lavanderia_id)
    except IntegrityError:
        raise ValueError(f"Ya existe un rol con el nombre '{clean}'.")


def toggle_role_status(role_id, lavanderia_id=None):
    """Activa o desactiva un rol."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    toggle_role(role_id, lavanderia_id=target_lavanderia_id)


def save_role_permissions(role_name, permissions, lavanderia_id=None):
    """Guarda los permisos de un rol, reemplazando los anteriores."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    set_permissions_for_role(role_name, permissions, lavanderia_id=target_lavanderia_id)


# --- Usuarios ---


def add_user(name, role, password, lavanderia_id=None):
    """Valida y crea un nuevo usuario con contrasena. Devuelve su id."""
    clean_name = _validate_name(name)
    clean_password = _validate_password(password)
    if not role or not role.strip():
        raise ValueError("El rol es obligatorio.")

    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        return create_user(
            clean_name,
            role.strip(),
            hash_password(clean_password),
            lavanderia_id=target_lavanderia_id,
        )
    except IntegrityError:
        raise ValueError(f"Ya existe un usuario con el nombre '{clean_name}'.")


def edit_user(user_id, name, role, lavanderia_id=None):
    """Valida y actualiza nombre y rol de un usuario."""
    clean_name = _validate_name(name)
    if not role or not role.strip():
        raise ValueError("El rol es obligatorio.")

    target_lavanderia_id = _require_tenant(lavanderia_id)
    try:
        update_user(
            user_id,
            clean_name,
            role.strip(),
            lavanderia_id=target_lavanderia_id,
        )
    except IntegrityError:
        raise ValueError(f"Ya existe un usuario con el nombre '{clean_name}'.")


def change_user_password(user_id, password, lavanderia_id=None):
    """Valida y actualiza la contrasena de un usuario."""
    clean = _validate_password(password)
    target_lavanderia_id = _require_tenant(lavanderia_id)
    update_user_password(
        user_id,
        hash_password(clean),
        lavanderia_id=target_lavanderia_id,
    )


def toggle_user_status(user_id, lavanderia_id=None):
    """Activa o desactiva un usuario."""
    target_lavanderia_id = _require_tenant(lavanderia_id)
    toggle_user(user_id, lavanderia_id=target_lavanderia_id)
