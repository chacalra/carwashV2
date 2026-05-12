"""Tests para services/client_service.py."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.services.client_service import (
    edit_client,
    find_client_by_ruc_ci,
    get_clients,
    register_client,
    toggle_client_status,
)


def _fake_session():
    return type(
        "FakeSession",
        (),
        {
            "commit": lambda self: None,
            "__enter__": lambda self: self,
            "__exit__": lambda self, exc_type, exc, tb: False,
        },
    )()


def test_get_clients_serializes_rows():
    fake_client = SimpleNamespace(
        id=2,
        nombre="Ana",
        tipo_cliente="particular",
        ruc_ci=None,
        telefono="0981000000",
        email=None,
        estado=True,
        created_at=None,
        lavanderia_id=3,
    )

    with patch("backend.services.client_service.SessionLocal", return_value=_fake_session()):
        with patch("backend.services.client_service.list_clients", return_value=[fake_client]):
            result = get_clients(3, only_active=True)

    assert result == [
        {
            "id": 2,
            "name": "Ana",
            "client_type": "particular",
            "ruc_ci": None,
            "phone": "0981000000",
            "email": None,
            "is_active": True,
            "created_at": None,
            "lavanderia_id": 3,
        }
    ]


def test_find_client_by_ruc_ci_returns_none_for_blank_value():
    assert find_client_by_ruc_ci(1, "   ") is None


def test_register_client_rejects_duplicate_ruc_ci():
    fake_session = _fake_session()
    existing_client = SimpleNamespace(id=8)

    with patch("backend.services.client_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.client_service.get_client_by_ruc_ci", return_value=existing_client):
            with pytest.raises(ValueError, match="Ya existe un cliente con ese RUC/CI"):
                register_client(
                    1,
                    "Acme SA",
                    "empresa",
                    ruc_ci="80012345-6",
                )


def test_edit_client_returns_client_id():
    fake_session = _fake_session()
    existing_client = SimpleNamespace(id=9)

    with patch("backend.services.client_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.client_service.get_client_by_id", return_value=existing_client):
            with patch("backend.services.client_service.get_client_by_ruc_ci", return_value=None):
                with patch("backend.services.client_service.update_client"):
                    client_id = edit_client(
                        1,
                        9,
                        "Acme SA",
                        "empresa",
                        ruc_ci="80012345-6",
                    )

    assert client_id == 9


def test_toggle_client_status_returns_client_id():
    fake_session = _fake_session()
    existing_client = SimpleNamespace(id=11, estado=True)

    with patch("backend.services.client_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.client_service.get_client_by_id", return_value=existing_client):
            with patch("backend.services.client_service.set_client_status"):
                client_id = toggle_client_status(1, 11)

    assert client_id == 11
