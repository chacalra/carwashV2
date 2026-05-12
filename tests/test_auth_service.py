"""Tests para services/auth_service.py."""

import pytest
from types import SimpleNamespace
from unittest.mock import patch
from backend.utils.security import hash_password
from backend.services.auth_service import get_allowed_views, login, PERMISSIONS, VIEW_PERMISSIONS


# --- get_allowed_views ---

def test_get_allowed_views_todos_los_permisos():
    all_perms = list(PERMISSIONS.keys())
    views = get_allowed_views(all_perms)
    assert set(views) == set(VIEW_PERMISSIONS.keys())


def test_get_allowed_views_un_permiso():
    views = get_allowed_views(["dashboard"])
    assert views == ["Dashboard"]


def test_get_allowed_views_vacio():
    assert get_allowed_views([]) == []


def test_get_allowed_views_permiso_inexistente():
    assert get_allowed_views(["permiso_falso"]) == []


# --- login ---

def test_login_nombre_vacio():
    with pytest.raises(ValueError, match="nombre de usuario"):
        login("", "password")


def test_login_nombre_solo_espacios():
    with pytest.raises(ValueError, match="nombre de usuario"):
        login("   ", "password")


def test_login_contrasena_vacia():
    with pytest.raises(ValueError, match="contrasena"):
        login("admin", "")


def test_login_sin_contexto_de_tenant():
    with pytest.raises(ValueError, match="host o subdominio"):
        login("admin", "password")


def test_login_usuario_no_encontrado():
    fake_tenant = SimpleNamespace(id=1, estado=True)
    with patch("backend.services.auth_service.get_tenant_by_subdominio", return_value=fake_tenant):
        with patch("backend.services.auth_service.get_user_by_name", return_value=None):
            with pytest.raises(ValueError, match="incorrectos"):
                login("noexiste", "pass", subdominio="demo")


def test_login_lavanderia_inactiva():
    fake_tenant = SimpleNamespace(id=1, estado=False)
    with patch("backend.services.auth_service.get_tenant_by_subdominio", return_value=fake_tenant):
        with pytest.raises(ValueError, match="no esta activa"):
            login("admin", "pass", subdominio="demo")


def test_login_usuario_no_encontrado_por_host():
    fake_tenant = SimpleNamespace(id=1, estado=True)
    with patch("backend.services.auth_service.get_tenant_by_host", return_value=fake_tenant):
        with patch("backend.services.auth_service.get_user_by_name", return_value=None):
            with pytest.raises(ValueError, match="incorrectos"):
                login("noexiste", "pass", host="demo.mukusoft.com")


def test_login_usuario_inactivo():
    fake_tenant = SimpleNamespace(id=1, estado=True)
    fake_user = {
        "id": 1, "name": "test", "role": "operador",
        "is_active": 0, "password_hash": "salt:hash"
    }
    with patch("backend.services.auth_service.get_tenant_by_subdominio", return_value=fake_tenant):
        with patch("backend.services.auth_service.get_user_by_name", return_value=fake_user):
            with pytest.raises(ValueError, match="incorrectos"):
                login("test", "pass", subdominio="demo")


def test_login_sin_contrasena_configurada():
    fake_tenant = SimpleNamespace(id=1, estado=True)
    fake_user = {
        "id": 1, "name": "test", "role": "operador",
        "is_active": 1, "password_hash": None
    }
    with patch("backend.services.auth_service.get_tenant_by_subdominio", return_value=fake_tenant):
        with patch("backend.services.auth_service.get_user_by_name", return_value=fake_user):
            with pytest.raises(ValueError, match="sin contrasena"):
                login("test", "pass", subdominio="demo")


def test_login_contrasena_incorrecta():
    fake_tenant = SimpleNamespace(id=1, estado=True)
    pw_hash = hash_password("correcta")
    fake_user = {
        "id": 1, "name": "admin", "role": "maximo",
        "is_active": 1, "password_hash": pw_hash, "role_id": 7
    }
    with patch("backend.services.auth_service.get_tenant_by_subdominio", return_value=fake_tenant):
        with patch("backend.services.auth_service.get_user_by_name", return_value=fake_user):
            with pytest.raises(ValueError, match="incorrectos"):
                login("admin", "incorrecta", subdominio="demo")


def test_login_exitoso():
    fake_tenant = SimpleNamespace(id=1, estado=True)
    pw_hash = hash_password("correcta")
    fake_user = {
        "id": 1, "name": "admin", "role": "maximo",
        "is_active": 1, "password_hash": pw_hash, "role_id": 7
    }
    with patch("backend.services.auth_service.get_tenant_by_subdominio", return_value=fake_tenant):
        with patch("backend.services.auth_service.get_user_by_name", return_value=fake_user):
            with patch("backend.services.auth_service.get_permissions_for_role", return_value=["dashboard", "settings"]):
                user, perms = login("admin", "correcta", subdominio="demo")
                assert user["name"] == "admin"
                assert "dashboard" in perms
                assert "settings" in perms
