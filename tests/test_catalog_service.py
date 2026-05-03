"""Tests para services/catalog_service.py."""

import pytest
import sqlite3
from unittest.mock import patch
from services.catalog_service import (
    _validate_name,
    _validate_password,
    add_service,
    rename_service,
    add_category,
    add_vehicle_type,
    add_role,
    add_user,
    change_user_password,
    remove_category,
    remove_product,
    remove_service,
    remove_vehicle_type,
    toggle_service_status,
    toggle_category_status,
    toggle_vehicle_type_status,
    toggle_role_status,
    toggle_user_status,
    save_role_permissions,
)


# --- _validate_name ---

def test_validate_name_valido():
    assert _validate_name("  Lavado  ") == "Lavado"


def test_validate_name_vacio():
    with pytest.raises(ValueError, match="vacio"):
        _validate_name("")


def test_validate_name_solo_espacios():
    with pytest.raises(ValueError, match="vacio"):
        _validate_name("   ")


def test_validate_name_no_string():
    with pytest.raises(ValueError):
        _validate_name(None)


# --- _validate_password ---

def test_validate_password_valida():
    assert _validate_password("1234") == "1234"


def test_validate_password_con_espacios():
    assert _validate_password("  pass  ") == "pass"


def test_validate_password_muy_corta():
    with pytest.raises(ValueError, match="4 caracteres"):
        _validate_password("abc")


def test_validate_password_vacia():
    with pytest.raises(ValueError):
        _validate_password("")


# --- add_service ---

def test_add_service_exitoso():
    with patch("services.catalog_service.create_service", return_value=1) as mock:
        result = add_service("Lavado completo")
        mock.assert_called_once_with("Lavado completo")
        assert result == 1


def test_add_service_duplicado():
    with patch("services.catalog_service.create_service", side_effect=sqlite3.IntegrityError):
        with pytest.raises(ValueError, match="Ya existe"):
            add_service("Lavado completo")


def test_add_service_nombre_vacio():
    with pytest.raises(ValueError):
        add_service("")


# --- rename_service ---

def test_rename_service_exitoso():
    with patch("services.catalog_service.update_service_name") as mock:
        rename_service(1, "Nuevo nombre")
        mock.assert_called_once_with(1, "Nuevo nombre")


def test_rename_service_duplicado():
    with patch("services.catalog_service.update_service_name", side_effect=sqlite3.IntegrityError):
        with pytest.raises(ValueError, match="Ya existe"):
            rename_service(1, "Duplicado")


# --- add_category / add_vehicle_type / add_role (misma logica) ---

def test_add_category_exitosa():
    with patch("services.catalog_service.create_category", return_value=2) as mock:
        result = add_category("Combustible")
        mock.assert_called_once_with("Combustible")
        assert result == 2


def test_add_vehicle_type_exitoso():
    with patch("services.catalog_service.create_vehicle_type", return_value=3) as mock:
        result = add_vehicle_type("Camion")
        mock.assert_called_once_with("Camion")
        assert result == 3


def test_add_role_exitoso():
    with patch("services.catalog_service.create_role", return_value=4) as mock:
        result = add_role("supervisor")
        mock.assert_called_once_with("supervisor")
        assert result == 4


# --- add_user ---

def test_add_user_rol_vacio():
    with pytest.raises(ValueError, match="rol"):
        add_user("Juan", "", "pass1234")


def test_add_user_rol_espacios():
    with pytest.raises(ValueError, match="rol"):
        add_user("Juan", "   ", "pass1234")


def test_add_user_contrasena_corta():
    with pytest.raises(ValueError, match="4 caracteres"):
        add_user("Juan", "operador", "123")


def test_add_user_exitoso():
    with patch("services.catalog_service.create_user", return_value=5) as mock:
        result = add_user("Juan", "operador", "pass1234")
        assert result == 5
        args = mock.call_args[0]
        assert args[0] == "Juan"
        assert args[1] == "operador"
        assert ":" in args[2]  # password hasheada


def test_add_user_nombre_vacio():
    with pytest.raises(ValueError):
        add_user("", "operador", "pass1234")


# --- change_user_password ---

def test_change_user_password_corta():
    with pytest.raises(ValueError, match="4 caracteres"):
        change_user_password(1, "abc")


def test_change_user_password_exitosa():
    with patch("services.catalog_service.update_user_password") as mock:
        change_user_password(1, "nueva_pass")
        mock.assert_called_once()
        args = mock.call_args[0]
        assert args[0] == 1
        assert ":" in args[1]  # hasheada


# --- toggles (delegan directo al repo, solo verificar que llaman correctamente) ---

def test_toggle_service_status():
    with patch("services.catalog_service.toggle_service") as mock:
        toggle_service_status(3)
        mock.assert_called_once_with(3)


def test_toggle_role_status():
    with patch("services.catalog_service.toggle_role") as mock:
        toggle_role_status(2)
        mock.assert_called_once_with(2)


# --- save_role_permissions ---

def test_save_role_permissions():
    with patch("services.catalog_service.set_permissions_for_role") as mock:
        save_role_permissions("operador", ["register_income"])
        mock.assert_called_once_with("operador", ["register_income"])


# --- remove_* (eliminar si no esta en uso, bloquear si esta en uso) ---

def test_remove_service_no_en_uso():
    with patch("services.catalog_service.is_service_in_use", return_value=False):
        with patch("services.catalog_service.delete_service") as mock_del:
            remove_service(1)
            mock_del.assert_called_once_with(1)


def test_remove_service_en_uso_lanza_error():
    with patch("services.catalog_service.is_service_in_use", return_value=True):
        with pytest.raises(ValueError, match="ingresos registrados"):
            remove_service(1)


def test_remove_product_no_en_uso():
    with patch("services.catalog_service.is_product_in_use", return_value=False):
        with patch("services.catalog_service.delete_product") as mock_del:
            remove_product(1)
            mock_del.assert_called_once_with(1)


def test_remove_product_en_uso_lanza_error():
    with patch("services.catalog_service.is_product_in_use", return_value=True):
        with pytest.raises(ValueError, match="ingresos registrados"):
            remove_product(1)


def test_remove_category_no_en_uso():
    with patch("services.catalog_service.is_category_in_use", return_value=False):
        with patch("services.catalog_service.delete_category") as mock_del:
            remove_category(1)
            mock_del.assert_called_once_with(1)


def test_remove_category_en_uso_lanza_error():
    with patch("services.catalog_service.is_category_in_use", return_value=True):
        with pytest.raises(ValueError, match="egresos registrados"):
            remove_category(1)


def test_remove_vehicle_type_no_en_uso():
    with patch("services.catalog_service.is_vehicle_type_in_use", return_value=False):
        with patch("services.catalog_service.delete_vehicle_type") as mock_del:
            remove_vehicle_type(1)
            mock_del.assert_called_once_with(1)


def test_remove_vehicle_type_en_uso_lanza_error():
    with patch("services.catalog_service.is_vehicle_type_in_use", return_value=True):
        with pytest.raises(ValueError, match="vehiculos registrados"):
            remove_vehicle_type(1)
