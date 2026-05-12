"""Tests para operations puntuales de services/sale_service.py."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.services.sale_service import (
    _resolve_sale_client,
    edit_sale,
    remove_sale,
    update_sale_payment_type,
    validate_sale_data,
)


def test_update_sale_payment_type_ok():
    fake_sale = SimpleNamespace(tipo_cobro="Contado", estado=True)
    fake_session = type(
        "FakeSession",
        (),
        {
            "commit": lambda self: None,
            "__enter__": lambda self: self,
            "__exit__": lambda self, exc_type, exc, tb: False,
        },
    )()

    with patch("backend.services.sale_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.sale_service.get_sale_by_id", return_value=fake_sale):
            update_sale_payment_type(1, 55, "Credito")

    assert fake_sale.tipo_cobro == "Credito"


def test_update_sale_payment_type_inexistente():
    fake_session = type(
        "FakeSession",
        (),
        {
            "commit": lambda self: None,
            "__enter__": lambda self: self,
            "__exit__": lambda self, exc_type, exc, tb: False,
        },
    )()

    with patch("backend.services.sale_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.sale_service.get_sale_by_id", return_value=None):
            with pytest.raises(ValueError, match="no existe"):
                update_sale_payment_type(1, 55, "Credito")


def test_remove_sale_inexistente():
    fake_session = type(
        "FakeSession",
        (),
        {
            "commit": lambda self: None,
            "__enter__": lambda self: self,
            "__exit__": lambda self, exc_type, exc, tb: False,
        },
    )()

    with patch("backend.services.sale_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.sale_service.get_sale_by_id", return_value=None):
            with pytest.raises(ValueError, match="no existe"):
                remove_sale(1, 99)


def test_edit_sale_inexistente():
    fake_session = type(
        "FakeSession",
        (),
        {
            "commit": lambda self: None,
            "__enter__": lambda self: self,
            "__exit__": lambda self, exc_type, exc, tb: False,
        },
    )()

    with patch("backend.services.sale_service.SessionLocal", return_value=fake_session):
        with patch("backend.services.sale_service.get_sale_by_id", return_value=None):
            with pytest.raises(ValueError, match="no existe"):
                edit_sale(
                    1,
                    55,
                    2,
                    "2026-05-03",
                    "Contado",
                    [{"servicio_id": 1, "cantidad": 1}],
                )


def test_validate_sale_data_rechaza_dos_servicios():
    fake_session = object()

    with patch("backend.services.sale_service._get_active_client", return_value=SimpleNamespace(id=8)):
        with patch("backend.services.sale_service._get_active_user", return_value=SimpleNamespace(id=2)):
            with patch("backend.services.sale_service._get_valid_vehicle", return_value=None):
                with patch(
                    "backend.services.sale_service._build_sale_item",
                    side_effect=[
                        {
                            "cantidad": 1,
                            "precio_unitario": 10000,
                            "subtotal": 10000,
                            "servicio_id": 1,
                            "producto_id": None,
                        },
                        {
                            "cantidad": 1,
                            "precio_unitario": 20000,
                            "subtotal": 20000,
                            "servicio_id": 2,
                            "producto_id": None,
                        },
                    ],
                ):
                    with pytest.raises(ValueError, match="maximo un servicio principal"):
                        validate_sale_data(
                            fake_session,
                            lavanderia_id=1,
                            usuario_id=2,
                            cliente_id=8,
                            fecha_venta="2026-05-03",
                            tipo_cobro="Contado",
                            items=[{"servicio_id": 1}, {"servicio_id": 2}],
                        )


def test_validate_sale_data_rechaza_producto_duplicado():
    fake_session = object()

    with patch("backend.services.sale_service._get_active_client", return_value=SimpleNamespace(id=8)):
        with patch("backend.services.sale_service._get_active_user", return_value=SimpleNamespace(id=2)):
            with patch("backend.services.sale_service._get_valid_vehicle", return_value=None):
                with patch(
                    "backend.services.sale_service._build_sale_item",
                    side_effect=[
                        {
                            "cantidad": 2,
                            "precio_unitario": 10000,
                            "subtotal": 20000,
                            "servicio_id": None,
                            "producto_id": 4,
                        },
                        {
                            "cantidad": 1,
                            "precio_unitario": 10000,
                            "subtotal": 10000,
                            "servicio_id": None,
                            "producto_id": 4,
                        },
                    ],
                ):
                    with pytest.raises(ValueError, match="producto debe cargarse"):
                        validate_sale_data(
                            fake_session,
                            lavanderia_id=1,
                            usuario_id=2,
                            cliente_id=8,
                            fecha_venta="2026-05-03",
                            tipo_cobro="Contado",
                            items=[{"producto_id": 4}, {"producto_id": 4}],
                        )


def test_validate_sale_data_rechaza_cantidad_mayor_a_uno_en_servicio():
    fake_service = SimpleNamespace(id=1, lavanderia_id=1, estado=True, precio=15000)

    class FakeSession:
        def scalar(self, query):
            return fake_service

    with pytest.raises(ValueError, match="servicio principal debe registrarse una sola vez"):
        validate_sale_data(
            FakeSession(),
            lavanderia_id=1,
            usuario_id=2,
            cliente_id=8,
            fecha_venta="2026-05-03",
            tipo_cobro="Contado",
            items=[{"servicio_id": 1, "cantidad": 2}],
            metodo_pago=None,
            requiere_factura=False,
            observacion=None,
            vehiculo_id=None,
        )


def test_resolve_sale_client_reutiliza_cliente_existente_para_factura():
    existing_client = SimpleNamespace(id=8, estado=True, nombre="Acme SA", ruc_ci="80012345-6")

    with patch("backend.services.sale_service.get_client_by_ruc_ci", return_value=existing_client):
        resolved = _resolve_sale_client(
            object(),
            lavanderia_id=1,
            client_id=None,
            requiere_factura=True,
            ruc_ci="80012345-6",
            razon_social="Acme SA",
        )

    assert resolved is existing_client


def test_resolve_sale_client_crea_cliente_facturable_si_no_existe():
    created_client = SimpleNamespace(id=11, estado=True, nombre="Nueva Empresa", ruc_ci="80123456-7")

    with patch("backend.services.sale_service.get_client_by_ruc_ci", return_value=None):
        with patch("backend.services.sale_service.create_client", return_value=created_client) as mock_create:
            resolved = _resolve_sale_client(
                object(),
                lavanderia_id=1,
                client_id=None,
                requiere_factura=True,
                ruc_ci="80123456-7",
                razon_social="Nueva Empresa",
            )

    assert resolved is created_client
    assert mock_create.call_args.kwargs["lavanderia_id"] == 1
    assert mock_create.call_args.kwargs["nombre"] == "Nueva Empresa"
    assert mock_create.call_args.kwargs["tipo_cliente"] == "empresa"
    assert mock_create.call_args.kwargs["ruc_ci"] == "80123456-7"


def test_resolve_sale_client_usa_cliente_del_vehiculo_en_venta_rapida():
    vehicle = SimpleNamespace(id=5, cliente_id=12)
    vehicle_client = SimpleNamespace(
        id=12,
        lavanderia_id=1,
        estado=True,
        tipo_cliente="particular",
        ruc_ci=None,
    )

    class FakeSession:
        def get(self, model, entity_id):
            return vehicle_client if entity_id == 12 else None

    resolved = _resolve_sale_client(
        FakeSession(),
        lavanderia_id=1,
        client_id=None,
        requiere_factura=False,
        vehicle=vehicle,
    )

    assert resolved is vehicle_client


def test_resolve_sale_client_rechaza_cliente_explicito_distinto_al_del_vehiculo():
    vehicle = SimpleNamespace(id=5, cliente_id=12)

    with patch(
        "backend.services.sale_service._get_active_client",
        return_value=SimpleNamespace(id=9, lavanderia_id=1, estado=True),
    ):
        with pytest.raises(ValueError, match="pertenece a otro cliente"):
            _resolve_sale_client(
                object(),
                lavanderia_id=1,
                client_id=9,
                requiere_factura=False,
                vehicle=vehicle,
            )


def test_resolve_sale_client_rechaza_factura_sin_ruc():
    with pytest.raises(ValueError, match="RUC/CI"):
        _resolve_sale_client(
            object(),
            lavanderia_id=1,
            client_id=None,
            requiere_factura=True,
            ruc_ci="",
            razon_social="Empresa SA",
        )


def test_resolve_sale_client_rechaza_factura_sin_razon_social():
    with pytest.raises(ValueError, match="Razon Social"):
        _resolve_sale_client(
            object(),
            lavanderia_id=1,
            client_id=None,
            requiere_factura=True,
            ruc_ci="80012345-6",
            razon_social="",
        )


# --- Regla: vehiculo acoplado a servicios ---


def _validate_with_items(items, vehicle, vehiculo_id):
    """Helper que ejecuta validate_sale_data con todos los validadores externos mockeados.

    `items` aquí ya viene 'normalizado' (lo que devolveria _build_sale_item).
    """
    fake_session = object()

    with patch("backend.services.sale_service._get_active_client", return_value=SimpleNamespace(id=8)), \
         patch("backend.services.sale_service._resolve_sale_client", return_value=SimpleNamespace(id=8)), \
         patch("backend.services.sale_service._get_active_user", return_value=SimpleNamespace(id=2)), \
         patch("backend.services.sale_service._get_valid_vehicle", return_value=vehicle), \
         patch("backend.services.sale_service._build_sale_item", side_effect=items):
        return validate_sale_data(
            fake_session,
            lavanderia_id=1,
            usuario_id=2,
            cliente_id=8,
            fecha_venta="2026-05-03",
            tipo_cobro="Contado",
            items=[{} for _ in items],
            vehiculo_id=vehiculo_id,
        )


def _service_item():
    return {
        "cantidad": 1,
        "precio_unitario": 50000,
        "subtotal": 50000,
        "servicio_id": 1,
        "producto_id": None,
    }


def _product_item(pid=4):
    return {
        "cantidad": 1,
        "precio_unitario": 12000,
        "subtotal": 12000,
        "servicio_id": None,
        "producto_id": pid,
    }


def test_venta_con_servicio_sin_vehiculo_falla():
    with pytest.raises(ValueError, match="vehiculo cuando la venta incluye servicios"):
        _validate_with_items(
            items=[_service_item()],
            vehicle=None,
            vehiculo_id=None,
        )


def test_venta_solo_productos_con_vehiculo_falla():
    vehicle = SimpleNamespace(id=9, estado=True, cliente_id=None, lavanderia_id=1)
    with pytest.raises(ValueError, match="no aplica para ventas de solo productos"):
        _validate_with_items(
            items=[_product_item()],
            vehicle=vehicle,
            vehiculo_id=9,
        )


def test_venta_con_servicio_y_vehiculo_pasa():
    vehicle = SimpleNamespace(id=9, estado=True, cliente_id=None, lavanderia_id=1)
    result = _validate_with_items(
        items=[_service_item()],
        vehicle=vehicle,
        vehiculo_id=9,
    )
    assert result["vehiculo_id"] == 9


def test_venta_solo_productos_sin_vehiculo_pasa():
    result = _validate_with_items(
        items=[_product_item()],
        vehicle=None,
        vehiculo_id=None,
    )
    assert result["vehiculo_id"] is None


def test_venta_mezcla_servicio_y_producto_requiere_vehiculo():
    vehicle = SimpleNamespace(id=9, estado=True, cliente_id=None, lavanderia_id=1)
    result = _validate_with_items(
        items=[_service_item(), _product_item()],
        vehicle=vehicle,
        vehiculo_id=9,
    )
    assert result["vehiculo_id"] == 9


def test_venta_mezcla_servicio_y_producto_sin_vehiculo_falla():
    with pytest.raises(ValueError, match="vehiculo cuando la venta incluye servicios"):
        _validate_with_items(
            items=[_service_item(), _product_item()],
            vehicle=None,
            vehiculo_id=None,
        )
