"""Tests unitarios V2 para repositories de ventas."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from repositories.sale_items_repository import (
    create_sale_item,
    create_sale_items,
    delete_sale_items,
)
from repositories.sales_repository import create_sale, delete_sale, update_sale


def test_create_sale_populates_entity_and_flushes():
    session = Mock()

    sale = create_sale(
        session,
        fecha_venta="2026-05-01",
        tipo_cobro="Contado",
        total=Decimal("150000.00"),
        cliente_id=7,
        lavanderia_id=3,
        usuario_id=5,
        metodo_pago="Efectivo",
        requiere_factura=False,
        observacion="Venta demo",
        vehiculo_id=11,
    )

    assert sale.fecha_venta == "2026-05-01"
    assert sale.tipo_cobro == "Contado"
    assert sale.total == Decimal("150000.00")
    assert sale.cliente_id == 7
    assert sale.lavanderia_id == 3
    assert sale.usuario_id == 5
    assert sale.metodo_pago == "Efectivo"
    assert sale.requiere_factura is False
    assert sale.observacion == "Venta demo"
    assert sale.vehiculo_id == 11
    session.add.assert_called_once_with(sale)
    session.flush.assert_called_once()


def test_update_sale_mutates_entity_and_flushes():
    session = Mock()
    sale = SimpleNamespace(
        fecha_venta=None,
        tipo_cobro=None,
        total=None,
        cliente_id=None,
        usuario_id=None,
        metodo_pago=None,
        requiere_factura=None,
        observacion=None,
        vehiculo_id=None,
    )

    updated = update_sale(
        session,
        sale,
        fecha_venta="2026-05-02",
        tipo_cobro="Credito",
        total=Decimal("89000.00"),
        cliente_id=9,
        usuario_id=4,
        metodo_pago="Transferencia",
        requiere_factura=True,
        observacion="Actualizada",
        vehiculo_id=2,
    )

    assert updated is sale
    assert sale.fecha_venta == "2026-05-02"
    assert sale.tipo_cobro == "Credito"
    assert sale.total == Decimal("89000.00")
    assert sale.cliente_id == 9
    assert sale.usuario_id == 4
    assert sale.metodo_pago == "Transferencia"
    assert sale.requiere_factura is True
    assert sale.observacion == "Actualizada"
    assert sale.vehiculo_id == 2
    session.flush.assert_called_once()


def test_delete_sale_deletes_entity_and_flushes():
    session = Mock()
    sale = SimpleNamespace(id=12)

    delete_sale(session, sale)

    session.delete.assert_called_once_with(sale)
    session.flush.assert_called_once()


def test_create_sale_item_populates_entity_and_flushes():
    session = Mock()

    item = create_sale_item(
        session,
        venta_id=15,
        cantidad=2,
        precio_unitario=Decimal("35000.00"),
        subtotal=Decimal("70000.00"),
        servicio_id=8,
        producto_id=None,
    )

    assert item.venta_id == 15
    assert item.cantidad == 2
    assert item.precio_unitario == Decimal("35000.00")
    assert item.subtotal == Decimal("70000.00")
    assert item.servicio_id == 8
    assert item.producto_id is None
    session.add.assert_called_once_with(item)
    session.flush.assert_called_once()


def test_create_sale_items_builds_multiple_rows():
    session = Mock()
    items = [
        {
            "cantidad": 1,
            "precio_unitario": Decimal("50000.00"),
            "subtotal": Decimal("50000.00"),
            "servicio_id": 3,
        },
        {
            "cantidad": 2,
            "precio_unitario": Decimal("12000.00"),
            "subtotal": Decimal("24000.00"),
            "producto_id": 9,
        },
    ]

    created = create_sale_items(session, 99, items)

    assert len(created) == 2
    assert created[0].venta_id == 99
    assert created[0].servicio_id == 3
    assert created[1].venta_id == 99
    assert created[1].producto_id == 9
    assert session.add.call_count == 2
    assert session.flush.call_count == 2


def test_delete_sale_items_deletes_all_related_rows():
    session = Mock()
    existing_items = [SimpleNamespace(id=1), SimpleNamespace(id=2)]

    with patch(
        "repositories.sale_items_repository.list_sale_items",
        return_value=existing_items,
    ) as mock_list:
        delete_sale_items(session, 44)

    mock_list.assert_called_once_with(session, 44)
    assert session.delete.call_count == 2
    session.delete.assert_any_call(existing_items[0])
    session.delete.assert_any_call(existing_items[1])
    session.flush.assert_called_once()
