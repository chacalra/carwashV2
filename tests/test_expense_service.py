"""Tests para services/expense_service.py."""

from unittest.mock import patch

import pytest

from services.expense_service import edit_expense, register_expense, validate_expense_data


def _make_category(active=True):
    return {
        "id": 9,
        "name": "Combustible",
        "estado": active,
        "is_active": 1 if active else 0,
    }


def test_validate_expense_data_ok():
    with patch("services.expense_service.resolve_lavanderia_id", return_value=3):
        with patch(
            "services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            result = validate_expense_data("2026-05-01", 9, 50000, "  carga  ")
            assert result["date"] == "2026-05-01"
            assert result["category_id"] == 9
            assert result["amount"] == 50000
            assert result["description"] == "carga"
            assert result["lavanderia_id"] == 3


def test_validate_expense_data_categoria_inactiva():
    with patch("services.expense_service.resolve_lavanderia_id", return_value=3):
        with patch(
            "services.expense_service.get_category_by_id",
            return_value=_make_category(active=False),
        ):
            with pytest.raises(ValueError, match="inactiva"):
                validate_expense_data("2026-05-01", 9, 50000, None)


def test_register_expense_pasa_tenant_y_user():
    with patch("services.expense_service.resolve_lavanderia_id", return_value=7):
        with patch(
            "services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            with patch("services.expense_service.create_expense", return_value=15) as mock_create:
                created_id = register_expense(
                    date="2026-05-01",
                    category_id=9,
                    amount=25000,
                    description="Taxi",
                    created_by="admin",
                    user_id=4,
                )

                assert created_id == 15
                mock_create.assert_called_once_with(
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
    with patch("services.expense_service.resolve_lavanderia_id", return_value=8):
        with patch(
            "services.expense_service.get_category_by_id",
            return_value=_make_category(active=True),
        ):
            with patch("services.expense_service.update_expense") as mock_update:
                edit_expense(
                    expense_id=99,
                    date="2026-05-02",
                    category_id=9,
                    amount=70000,
                    description="Proveedor",
                    has_iva=True,
                )
                mock_update.assert_called_once_with(
                    99,
                    "2026-05-02",
                    9,
                    70000,
                    "Proveedor",
                    has_iva=1,
                    lavanderia_id=8,
                )
