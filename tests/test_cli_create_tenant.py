"""Tests para backend/cli/create_tenant.py."""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.cli.create_tenant import (
    _create_tenant_in_session,
    create_tenant,
    normalize_subdomain,
)


# --- normalize_subdomain ---

def test_normalize_subdomain_lowercase_y_trim():
    assert normalize_subdomain("  Demo  ") == "demo"
    assert normalize_subdomain("AUTOCARE") == "autocare"


def test_normalize_subdomain_acepta_guiones_y_numeros():
    assert normalize_subdomain("la-vandra-2025") == "la-vandra-2025"


def test_normalize_subdomain_rechaza_caracteres_invalidos():
    with pytest.raises(ValueError, match="Subdominio inválido"):
        normalize_subdomain("demo cliente")
    with pytest.raises(ValueError, match="Subdominio inválido"):
        normalize_subdomain("demo.cliente")
    with pytest.raises(ValueError, match="Subdominio inválido"):
        normalize_subdomain("demo_cliente")


def test_normalize_subdomain_vacio_y_none():
    with pytest.raises(ValueError, match="obligatorio"):
        normalize_subdomain(None)
    with pytest.raises(ValueError, match="obligatorio"):
        normalize_subdomain("")
    with pytest.raises(ValueError, match="obligatorio"):
        normalize_subdomain("   ")


# --- _create_tenant_in_session ---

def _fake_session_with(monkeypatch, *, existing_subdomain=None, permisos=None):
    """Sesión mock + mocks de get_lavanderia_by_subdominio y create_lavanderia.

    `permisos` es una lista de Permiso-like objects (SimpleNamespace con id).
    Por default devuelve 8 permisos (uno por cada del catálogo real).
    """
    if permisos is None:
        permisos = [SimpleNamespace(id=i + 1, codigo=f"perm_{i}") for i in range(8)]

    session = MagicMock()
    # session.scalars(...).all() devuelve la lista de permisos
    session.scalars.return_value.all.return_value = permisos

    # Lavandería simulada que devuelve create_lavanderia (con id ya asignado)
    created_lav = SimpleNamespace(
        id=42,
        subdominio="demo",
        nombre_local="Lavandería Demo",
        nombre_responsable="Ana",
        email=None,
        telefono=None,
    )

    monkeypatch.setattr(
        "backend.cli.create_tenant.get_lavanderia_by_subdominio",
        lambda s, sub: SimpleNamespace(id=99) if sub == existing_subdomain else None,
    )

    def fake_create_lavanderia(s, **kwargs):
        created_lav.subdominio = kwargs["subdominio"]
        created_lav.nombre_local = kwargs["nombre_local"]
        created_lav.nombre_responsable = kwargs["nombre_responsable"]
        created_lav.email = kwargs.get("email")
        created_lav.telefono = kwargs.get("telefono")
        return created_lav

    monkeypatch.setattr(
        "backend.cli.create_tenant.create_lavanderia",
        fake_create_lavanderia,
    )

    # Cuando se hace flush sobre el rol o el usuario nuevo, asignar id.
    # Simulamos id incremental con un contador.
    counter = {"role": 7, "user": 11}

    def fake_flush():
        for call_args in session.add.call_args_list:
            obj = call_args[0][0]
            if obj.__class__.__name__ == "Rol" and getattr(obj, "id", None) is None:
                obj.id = counter["role"]
            if obj.__class__.__name__ == "Usuario" and getattr(obj, "id", None) is None:
                obj.id = counter["user"]

    session.flush.side_effect = fake_flush
    return session, permisos, created_lav


def test_create_tenant_happy_path(monkeypatch):
    session, permisos, created_lav = _fake_session_with(monkeypatch)

    result = _create_tenant_in_session(
        session,
        subdomain="Demo",
        name="Lavandería Demo",
        responsible="Ana Pérez",
        admin_username="admin",
        admin_password="superseguro",
        email="ana@demo.com",
        phone="0991-000",
    )

    assert result["subdominio"] == "demo"
    assert result["lavanderia_id"] == 42
    assert result["role_name"] == "admin"
    assert result["role_id"] == 7
    assert result["admin_user_id"] == 11
    assert result["admin_username"] == "admin"
    assert result["permissions_count"] == len(permisos)
    assert result["email"] == "ana@demo.com"

    # Se agregó: 1 rol + N permisos (RolPermiso) + 1 usuario
    added_classes = [c[0][0].__class__.__name__ for c in session.add.call_args_list]
    assert added_classes.count("Rol") == 1
    assert added_classes.count("RolPermiso") == len(permisos)
    assert added_classes.count("Usuario") == 1

    # El password no se almacena en claro
    usuario = next(c[0][0] for c in session.add.call_args_list if c[0][0].__class__.__name__ == "Usuario")
    assert usuario.password_hash != "superseguro"
    assert ":" in usuario.password_hash  # formato salt:hash


def test_create_tenant_normaliza_subdomain(monkeypatch):
    session, _, _ = _fake_session_with(monkeypatch)
    result = _create_tenant_in_session(
        session,
        subdomain="  AutoCare-2025  ",
        name="x",
        responsible="y",
        admin_username="a",
        admin_password="12345678",
    )
    assert result["subdominio"] == "autocare-2025"


def test_create_tenant_falla_si_subdomain_ya_existe(monkeypatch):
    session, _, _ = _fake_session_with(monkeypatch, existing_subdomain="demo")

    with pytest.raises(ValueError, match="Ya existe un tenant"):
        _create_tenant_in_session(
            session,
            subdomain="demo",
            name="x",
            responsible="y",
            admin_username="a",
            admin_password="12345678",
        )


def test_create_tenant_password_corta(monkeypatch):
    session, _, _ = _fake_session_with(monkeypatch)
    with pytest.raises(ValueError, match="al menos"):
        _create_tenant_in_session(
            session,
            subdomain="demo",
            name="x",
            responsible="y",
            admin_username="a",
            admin_password="short",
        )


def test_create_tenant_password_vacia(monkeypatch):
    session, _, _ = _fake_session_with(monkeypatch)
    with pytest.raises(ValueError, match="contraseña"):
        _create_tenant_in_session(
            session,
            subdomain="demo",
            name="x",
            responsible="y",
            admin_username="a",
            admin_password="",
        )


def test_create_tenant_campos_obligatorios(monkeypatch):
    session, _, _ = _fake_session_with(monkeypatch)

    with pytest.raises(ValueError, match="nombre de la lavandería"):
        _create_tenant_in_session(
            session, subdomain="demo", name="  ",
            responsible="y", admin_username="a", admin_password="12345678",
        )
    with pytest.raises(ValueError, match="responsable"):
        _create_tenant_in_session(
            session, subdomain="demo", name="x",
            responsible="", admin_username="a", admin_password="12345678",
        )
    with pytest.raises(ValueError, match="usuario admin"):
        _create_tenant_in_session(
            session, subdomain="demo", name="x",
            responsible="y", admin_username="", admin_password="12345678",
        )


def test_create_tenant_falla_sin_permisos_en_catalogo(monkeypatch):
    session, _, _ = _fake_session_with(monkeypatch, permisos=[])

    with pytest.raises(ValueError, match="No hay permisos activos"):
        _create_tenant_in_session(
            session,
            subdomain="demo",
            name="x",
            responsible="y",
            admin_username="a",
            admin_password="12345678",
        )


# --- create_tenant (wrapper público): rollback en error ---

def test_create_tenant_rollback_si_falla(monkeypatch):
    """Si _create_tenant_in_session levanta, el wrapper hace rollback."""
    session = MagicMock()
    session_factory = MagicMock(return_value=session)

    monkeypatch.setattr("backend.cli.create_tenant.SessionLocal", session_factory)
    monkeypatch.setattr(
        "backend.cli.create_tenant._create_tenant_in_session",
        MagicMock(side_effect=ValueError("explosión")),
    )

    with pytest.raises(ValueError, match="explosión"):
        create_tenant(
            subdomain="demo",
            name="x",
            responsible="y",
            admin_username="a",
            admin_password="12345678",
        )

    session.rollback.assert_called_once()
    session.commit.assert_not_called()
    session.close.assert_called_once()


def test_create_tenant_commit_si_exito(monkeypatch):
    session = MagicMock()
    session_factory = MagicMock(return_value=session)

    monkeypatch.setattr("backend.cli.create_tenant.SessionLocal", session_factory)
    monkeypatch.setattr(
        "backend.cli.create_tenant._create_tenant_in_session",
        MagicMock(return_value={"lavanderia_id": 1}),
    )

    result = create_tenant(
        subdomain="demo",
        name="x",
        responsible="y",
        admin_username="a",
        admin_password="12345678",
    )

    assert result == {"lavanderia_id": 1}
    session.commit.assert_called_once()
    session.rollback.assert_not_called()
    session.close.assert_called_once()
