"""Tests para services/vehicle_service.py."""

from unittest.mock import patch

import pytest

from services.vehicle_service import normalize_plate, find_or_create_vehicle


# --- normalize_plate ---

def test_normalize_plate_mayusculas():
    assert normalize_plate("abc123") == "ABC123"


def test_normalize_plate_trim():
    assert normalize_plate("  ABC123  ") == "ABC123"


def test_normalize_plate_mixto():
    assert normalize_plate("  aBc 123  ") == "ABC 123"


# --- find_or_create_vehicle ---

def test_crea_vehiculo_nuevo():
    with patch("services.vehicle_service.resolve_lavanderia_id", return_value=3):
        with patch(
            "services.vehicle_service.get_vehicle_type_by_id",
            return_value={"id": 1, "estado": True},
        ):
            with patch("services.vehicle_service.find_vehicle_by_plate", return_value=None):
                with patch("services.vehicle_service.create_vehicle", return_value=42) as mock_create:
                    result = find_or_create_vehicle("abc123", 1, "Juan", "0981000000")
                    assert result == 42
                    mock_create.assert_called_once_with(
                        "ABC123",
                        1,
                        "Juan",
                        "0981000000",
                        lavanderia_id=3,
                    )


def test_actualiza_vehiculo_existente():
    existing = {"id": 7, "license_plate": "ABC123"}
    with patch("services.vehicle_service.resolve_lavanderia_id", return_value=5):
        with patch(
            "services.vehicle_service.get_vehicle_type_by_id",
            return_value={"id": 2, "estado": True},
        ):
            with patch("services.vehicle_service.find_vehicle_by_plate", return_value=existing):
                with patch("services.vehicle_service.update_vehicle") as mock_update:
                    result = find_or_create_vehicle("ABC123", 2, "Maria", "0982000000")
                    assert result == 7
                    mock_update.assert_called_once_with(
                        7,
                        2,
                        "Maria",
                        "0982000000",
                        lavanderia_id=5,
                    )


def test_normaliza_owner_con_espacios():
    with patch("services.vehicle_service.resolve_lavanderia_id", return_value=1):
        with patch(
            "services.vehicle_service.get_vehicle_type_by_id",
            return_value={"id": 1, "estado": True},
        ):
            with patch("services.vehicle_service.find_vehicle_by_plate", return_value=None):
                with patch("services.vehicle_service.create_vehicle", return_value=1) as mock_create:
                    find_or_create_vehicle("ABC123", 1, "  Juan  ", "  0981  ")
                    args = mock_create.call_args[0]
                    assert args[2] == "Juan"
                    assert args[3] == "0981"


def test_owner_vacio_se_convierte_en_none():
    with patch("services.vehicle_service.resolve_lavanderia_id", return_value=1):
        with patch(
            "services.vehicle_service.get_vehicle_type_by_id",
            return_value={"id": 1, "estado": True},
        ):
            with patch("services.vehicle_service.find_vehicle_by_plate", return_value=None):
                with patch("services.vehicle_service.create_vehicle", return_value=1) as mock_create:
                    find_or_create_vehicle("ABC123", 1, "   ", "   ")
                    args = mock_create.call_args[0]
                    assert args[2] is None
                    assert args[3] is None


def test_sin_owner_ni_phone():
    with patch("services.vehicle_service.resolve_lavanderia_id", return_value=1):
        with patch(
            "services.vehicle_service.get_vehicle_type_by_id",
            return_value={"id": 1, "estado": True},
        ):
            with patch("services.vehicle_service.find_vehicle_by_plate", return_value=None):
                with patch("services.vehicle_service.create_vehicle", return_value=1) as mock_create:
                    find_or_create_vehicle("ABC123", 1)
                    args = mock_create.call_args[0]
                    assert args[2] is None
                    assert args[3] is None


def test_tipo_vehiculo_inactivo_lanza_error():
    with patch("services.vehicle_service.resolve_lavanderia_id", return_value=1):
        with patch(
            "services.vehicle_service.get_vehicle_type_by_id",
            return_value={"id": 1, "estado": False},
        ):
            with pytest.raises(ValueError, match="inactivo"):
                find_or_create_vehicle("ABC123", 1)
