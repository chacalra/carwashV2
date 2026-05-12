"""Tests para la logica de estado de ui/sales_form.py."""

from frontend.streamlit.ui.sales_form import (
    LINE_COUNT_KEY,
    _get_available_line_capacity,
    _build_vehicle_payload,
    _get_current_item_type_from_state,
    _get_item_type_options_for_line,
    _get_product_options_for_line,
    _remove_line_from_state,
    _split_clients_for_sale,
    _service_selected_in_other_line_from_state,
)


def test_remove_line_from_state_compacts_middle_line():
    state = {
        LINE_COUNT_KEY: 3,
        "sales_item_type_0": "Servicio",
        "sales_item_name_0": "Lavado completo",
        "sales_item_price_0": 35000.0,
        "sales_item_type_1": "Producto",
        "sales_item_name_1": "Shampoo",
        "sales_item_qty_1": 2,
        "sales_item_price_1": 12000.0,
        "sales_item_type_2": "Producto",
        "sales_item_name_2": "Cera",
        "sales_item_qty_2": 1,
        "sales_item_price_2": 8000.0,
    }

    _remove_line_from_state(state, 1)

    assert state[LINE_COUNT_KEY] == 2
    assert state["sales_item_type_1"] == "Producto"
    assert state["sales_item_name_1"] == "Cera"
    assert state["sales_item_qty_1"] == 1
    assert state["sales_item_price_1"] == 8000.0
    assert "sales_item_type_2" not in state
    assert "sales_item_name_2" not in state
    assert "sales_item_qty_2" not in state
    assert "sales_item_price_2" not in state


def test_remove_line_from_state_does_nothing_with_single_line():
    state = {
        LINE_COUNT_KEY: 1,
        "sales_item_type_0": "Servicio",
        "sales_item_name_0": "Lavado completo",
    }

    _remove_line_from_state(state, 0)

    assert state[LINE_COUNT_KEY] == 1
    assert state["sales_item_type_0"] == "Servicio"
    assert state["sales_item_name_0"] == "Lavado completo"


def test_service_selected_in_other_line_from_state_detects_existing_service():
    state = {
        LINE_COUNT_KEY: 2,
        "sales_item_type_0": "Servicio",
        "sales_item_type_1": "Producto",
    }

    assert _service_selected_in_other_line_from_state(state, 1, 2) is True
    assert _service_selected_in_other_line_from_state(state, 0, 2) is False


def test_get_current_item_type_from_state_defaults_to_product_if_service_exists():
    state = {
        LINE_COUNT_KEY: 2,
        "sales_item_type_0": "Servicio",
    }

    assert _get_current_item_type_from_state(state, 1, 2) == "Producto"


def test_get_current_item_type_from_state_defaults_to_service_on_first_line():
    state = {LINE_COUNT_KEY: 1}

    assert _get_current_item_type_from_state(state, 0, 1) == "Servicio"


def test_get_available_line_capacity_counts_one_service_and_unique_products():
    services = [{"id": 1, "name": "Lavado"}]
    products = [{"id": 10, "name": "Perfume"}]

    assert _get_available_line_capacity(services, products) == 2
    assert _get_available_line_capacity([], products) == 1
    assert _get_available_line_capacity(services, []) == 1


def test_get_product_options_for_line_excludes_products_selected_elsewhere():
    products = [
        {"id": 10, "name": "Perfume"},
        {"id": 11, "name": "Cera"},
    ]
    state = {
        LINE_COUNT_KEY: 3,
        "sales_item_type_0": "Servicio",
        "sales_item_name_0": "Lavado",
        "sales_item_type_1": "Producto",
        "sales_item_name_1": "Perfume",
        "sales_item_type_2": "Producto",
        "sales_item_name_2": "Cera",
    }

    options_for_line_2 = _get_product_options_for_line(products, state, 2, 3)
    options_for_new_line = _get_product_options_for_line(products, state, 3, 3)

    assert [product["name"] for product in options_for_line_2] == ["Cera"]
    assert options_for_new_line == []


def test_get_item_type_options_for_line_blocks_second_service_and_duplicate_product():
    services = [{"id": 1, "name": "Lavado"}]
    state = {
        LINE_COUNT_KEY: 2,
        "sales_item_type_0": "Servicio",
        "sales_item_name_0": "Lavado",
        "sales_item_type_1": "Producto",
        "sales_item_name_1": "Perfume",
    }

    assert _get_item_type_options_for_line(
        state,
        1,
        2,
        services,
        [{"id": 10, "name": "Perfume"}],
    ) == ("Producto",)
    assert _get_item_type_options_for_line(state, 2, 2, services, []) == ()


def test_split_clients_for_sale_separates_generic_and_billable_clients():
    clients = [
        {"id": 1, "name": "Consumidor Final", "type": "generico", "ruc_ci": None},
        {"id": 2, "name": "Acme SA", "type": "empresa", "ruc_ci": "80012345-6"},
        {"id": 3, "name": "Juan Perez", "type": "particular", "ruc_ci": "4567890"},
        {"id": 4, "name": "Sin Documento", "type": "particular", "ruc_ci": None},
    ]

    generic_client, billable_clients = _split_clients_for_sale(clients)

    assert generic_client["id"] == 1
    assert [client["id"] for client in billable_clients] == [2, 3]


def test_build_vehicle_payload_returns_none_without_plate():
    assert _build_vehicle_payload("", 1, "Juan", "0981") is None
    assert _build_vehicle_payload("   ", 1) is None


def test_build_vehicle_payload_normalizes_optional_fields():
    payload = _build_vehicle_payload(" abc123 ", 4, "  Juan Perez ", " 0981 ")

    assert payload == {
        "license_plate": "abc123",
        "vehicle_type_id": 4,
        "owner_name": "Juan Perez",
        "phone": "0981",
    }


def test_build_vehicle_payload_requires_vehicle_type_with_plate():
    try:
        _build_vehicle_payload("ABC123", None)
    except ValueError as error:
        assert "tipo de vehiculo" in str(error)
    else:
        raise AssertionError("Expected ValueError")
