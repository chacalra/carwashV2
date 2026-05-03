"""Tests para services/income_service.py."""

import pytest
from unittest.mock import patch
from services.income_service import validate_income_data, register_income, edit_income


def _make_service(is_active=1):
    return {"id": 1, "name": "Lavado completo", "is_active": is_active}


# --- validate_income_data ---

def test_fecha_vacia():
    with pytest.raises(ValueError, match="fecha"):
        validate_income_data("", 1, 100, None, None)


def test_fecha_solo_espacios():
    with pytest.raises(ValueError, match="fecha"):
        validate_income_data("   ", 1, 100, None, None)


def test_servicio_none():
    with pytest.raises(ValueError, match="servicio o producto"):
        validate_income_data("2026-01-01", None, 100, None, None)


def test_servicio_no_existe():
    with patch("services.income_service.get_service_by_id", return_value=None):
        with pytest.raises(ValueError, match="no existe"):
            validate_income_data("2026-01-01", 99, 100, None, None)


def test_servicio_inactivo():
    with patch("services.income_service.get_service_by_id", return_value=_make_service(is_active=0)):
        with pytest.raises(ValueError, match="inactivo"):
            validate_income_data("2026-01-01", 1, 100, None, None)


def test_monto_cero():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="mayor que cero"):
            validate_income_data("2026-01-01", 1, 0, None, None)


def test_monto_negativo():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="mayor que cero"):
            validate_income_data("2026-01-01", 1, -50000, None, None)


def test_monto_none():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="mayor que cero"):
            validate_income_data("2026-01-01", 1, None, None, None)


def test_validacion_exitosa():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data("2026-01-01", 1, 50000, "Efectivo", " nota ")
        assert result["date"] == "2026-01-01"
        assert result["amount"] == 50000
        assert result["payment_method"] == "Efectivo"
        assert result["notes"] == "nota"


def test_payment_method_espacios_se_normaliza():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data("2026-01-01", 1, 50000, "  Transferencia  ", None)
        assert result["payment_method"] == "Transferencia"


def test_payment_method_vacio_queda_none():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data("2026-01-01", 1, 50000, "   ", None)
        assert result["payment_method"] is None


# --- register_income ---

def test_matricula_sin_tipo_vehiculo():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="tipo de vehiculo"):
            register_income("2026-01-01", 1, 50000, license_plate="ABC123", vehicle_type_id=None)


def test_register_sin_vehiculo():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with patch("services.income_service.create_income", return_value=1) as mock_create:
            register_income("2026-01-01", 1, 50000)
            args = mock_create.call_args[0]
            assert args[5] is None  # vehicle_id


def test_register_con_vehiculo():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with patch("services.income_service.find_or_create_vehicle", return_value=7) as mock_vehicle:
            with patch("services.income_service.create_income", return_value=1) as mock_create:
                register_income(
                    "2026-01-01", 1, 50000,
                    license_plate="ABC123", vehicle_type_id=2,
                    owner_name="Juan", phone="0981000000"
                )
                mock_vehicle.assert_called_once_with("ABC123", 2, "Juan", "0981000000")
                args = mock_create.call_args[0]
                assert args[5] == 7  # vehicle_id


# --- edit_income ---

def test_edit_income_matricula_sin_tipo():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="tipo de vehiculo"):
            edit_income(1, "2026-01-01", 1, 50000, license_plate="XYZ", vehicle_type_id=None)


def test_edit_income_exitoso():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with patch("services.income_service.update_income") as mock_update:
            edit_income(1, "2026-01-01", 1, 75000)
            mock_update.assert_called_once()


# --- payment_type ---

def test_payment_type_invalido():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="tipo de cobro"):
            validate_income_data("2026-01-01", 1, 50000, None, None, payment_type="Fiado")


def test_payment_type_default_contado():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data("2026-01-01", 1, 50000, None, None)
        assert result["payment_type"] == "Contado"


def test_payment_type_credito():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data("2026-01-01", 1, 50000, None, None, payment_type="Credito")
        assert result["payment_type"] == "Credito"


# --- factura ---

def test_factura_sin_ruc_lanza_error():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="RUC"):
            validate_income_data(
                "2026-01-01", 1, 50000, None, None,
                requires_invoice=True, ruc_ci="", razon_social="Empresa SA",
            )


def test_factura_sin_razon_social_lanza_error():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        with pytest.raises(ValueError, match="razon social"):
            validate_income_data(
                "2026-01-01", 1, 50000, None, None,
                requires_invoice=True, ruc_ci="80012345-6", razon_social="",
            )


def test_factura_completa_ok():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data(
            "2026-01-01", 1, 50000, None, None,
            requires_invoice=True, ruc_ci="80012345-6", razon_social="Empresa S.A.",
        )
        assert result["requires_invoice"] == 1
        assert result["ruc_ci"] == "80012345-6"
        assert result["razon_social"] == "Empresa S.A."


def test_sin_factura_ruc_queda_none():
    with patch("services.income_service.get_service_by_id", return_value=_make_service()):
        result = validate_income_data("2026-01-01", 1, 50000, None, None, requires_invoice=False)
        assert result["requires_invoice"] == 0
        assert result["ruc_ci"] is None
        assert result["razon_social"] is None
