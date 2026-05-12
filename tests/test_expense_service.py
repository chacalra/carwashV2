"""Tests para services/expense_service.py."""

from unittest.mock import MagicMock, patch

import pytest

from backend.services.expense_service import (
    edit_expense,
    get_expense,
    register_expense,
    remove_expense,
    validate_expense_data,
)


def _make_category(active=True):
    return {
        "id": 9,
        "name": "Combustible",
        "estado": active,
        "is_active": 1 if active else 0,
    }


def test_validate_expense_data_ok():
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=3):
        with patch(
            "backend.services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            result = validate_expense_data("2026-05-01", 9, 50000, "  carga  ")
            assert result["date"] == "2026-05-01"
            assert result["category_id"] == 9
            assert result["amount"] == 50000
            assert result["description"] == "carga"
            assert result["lavanderia_id"] == 3


def test_validate_expense_data_categoria_inactiva():
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=3):
        with patch(
            "backend.services.expense_service.get_category_by_id",
            return_value=_make_category(active=False),
        ):
            with pytest.raises(ValueError, match="inactiva"):
                validate_expense_data("2026-05-01", 9, 50000, None)


def test_register_expense_pasa_tenant_y_user():
    mock_session = MagicMock()
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=7):
        with patch(
            "backend.services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            with patch("backend.services.expense_service.create_expense", return_value=15) as mock_create:
                created_id = register_expense(
                    mock_session,
                    date="2026-05-01",
                    category_id=9,
                    amount=25000,
                    description="Taxi",
                    created_by="admin",
                    user_id=4,
                )

                assert created_id == 15
                mock_create.assert_called_once_with(
                    mock_session,
                    "2026-05-01",
                    9,
                    25000,
                    "Taxi",
                    created_by="admin",
                    has_iva=0,
                    lavanderia_id=7,
                    user_id=4,
                )


def test_edit_expense_pasa_tenant():
    mock_session = MagicMock()
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=8):
        with patch(
            "backend.services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            with patch("backend.services.expense_service.update_expense") as mock_update:
                edit_expense(
                    mock_session,
                    expense_id=99,
                    date="2026-05-02",
                    category_id=9,
                    amount=70000,
                    description="Proveedor",
                    has_iva=True,
                )
                mock_update.assert_called_once_with(
                    mock_session,
                    99,
                    "2026-05-02",
                    9,
                    70000,
                    "Proveedor",
                    has_iva=1,
                    lavanderia_id=8,
                )


def test_edit_expense_devuelve_id():
    mock_session = MagicMock()
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=8):
        with patch(
            "backend.services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            with patch("backend.services.expense_service.update_expense"):
                updated_id = edit_expense(
                    mock_session,
                    expense_id=99,
                    date="2026-05-02",
                    category_id=9,
                    amount=70000,
                    description="Proveedor",
                )

    assert updated_id == 99


def test_get_expense_pasa_tenant():
    expected = {"id": 55}
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=6):
        with patch("backend.services.expense_service.get_expense_by_id", return_value=expected) as mock_get:
            result = get_expense(55)

    assert result == expected
    mock_get.assert_called_once_with(55, lavanderia_id=6)


def test_remove_expense_pasa_tenant():
    mock_session = MagicMock()
    with patch("backend.services.expense_service.resolve_lavanderia_id", return_value=6):
        with patch("backend.services.expense_service.cancel_expense") as mock_cancel:
            remove_expense(mock_session, 55)

    mock_cancel.assert_called_once_with(mock_session, 55, lavanderia_id=6)
