"""Tests for the initial FastAPI surface."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.utils.security import create_access_token


def _client(monkeypatch):
    monkeypatch.setattr(
        "backend.api.deps.get_user_by_id",
        lambda user_id, lavanderia_id=None: {
            "id": user_id,
            "name": f"user-{user_id}",
            "role": "admin",
            "is_active": 1,
            "lavanderia_id": lavanderia_id,
            "lavanderia_name": f"Lavanderia {lavanderia_id}",
        },
    )
    return TestClient(create_app())


def _auth_headers(*permissions, user_id=7, lavanderia_id=3):
    token, _ = create_access_token(
        user_id=user_id,
        lavanderia_id=lavanderia_id,
        permissions=list(permissions),
    )
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_uses_subdominio_when_provided(monkeypatch):
    calls = {}

    def fake_login(username, password, *, subdominio=None, host=None):
        calls.update(
            {
                "username": username,
                "password": password,
                "subdominio": subdominio,
                "host": host,
            }
        )
        return (
            {
                "id": 7,
                "name": "admin",
                "role": "admin",
                "lavanderia_id": 3,
                "lavanderia_name": "Demo",
            },
            ["dashboard", "register_sale"],
        )

    monkeypatch.setattr("backend.api.routers.auth.authenticate_user", fake_login)

    response = _client(monkeypatch).post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "secret",
            "subdominio": "demo",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"] == {
        "id": 7,
        "username": "admin",
        "role": "admin",
        "lavanderia_id": 3,
        "lavanderia_name": "Demo",
    }
    assert body["permissions"] == ["dashboard", "register_sale"]
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_at"]
    assert calls == {
        "username": "admin",
        "password": "secret",
        "subdominio": "demo",
        "host": None,
    }


def test_login_uses_host_when_subdominio_is_missing(monkeypatch):
    calls = {}

    def fake_login(username, password, *, subdominio=None, host=None):
        calls.update({"subdominio": subdominio, "host": host})
        return (
            {
                "id": 8,
                "name": username,
                "role": "operador",
                "lavanderia_id": 4,
                "lavanderia_name": None,
            },
            ["dashboard"],
        )

    monkeypatch.setattr("backend.api.routers.auth.authenticate_user", fake_login)

    response = _client(monkeypatch).post(
        "/auth/login",
        headers={"Host": "demo.mukusoft.com"},
        json={"username": "operador", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "operador"
    assert calls == {
        "subdominio": None,
        "host": "demo.mukusoft.com",
    }


def test_login_maps_bad_credentials_to_unauthorized(monkeypatch):
    def fake_login(*args, **kwargs):
        raise ValueError("Usuario o contrasena incorrectos.")

    monkeypatch.setattr("backend.api.routers.auth.authenticate_user", fake_login)

    response = _client(monkeypatch).post(
        "/auth/login",
        json={"username": "admin", "password": "bad", "subdominio": "demo"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Usuario o contrasena incorrectos."}


def test_login_returns_full_tenant_when_present(monkeypatch):
    """Cuando el repo devuelve `tenant`, el response anida los campos de branding."""

    def fake_login(username, password, *, subdominio=None, host=None):
        return (
            {
                "id": 9,
                "name": username,
                "role": "admin",
                "lavanderia_id": 12,
                "lavanderia_name": "Autocare",
                "tenant": {
                    "id": 12,
                    "name": "Autocare",
                    "subdominio": "autocare",
                    "logo_url": "https://cdn.example/autocare.png",
                    "logo_url_dark": None,
                    "color_primario": "#FF0000",
                    "color_secundario": "#00FF00",
                    "mostrar_marca_mukusoft": False,
                },
            },
            ["dashboard"],
        )

    monkeypatch.setattr("backend.api.routers.auth.authenticate_user", fake_login)

    response = _client(monkeypatch).post(
        "/auth/login",
        json={"username": "admin", "password": "secret", "subdominio": "autocare"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tenant"] == {
        "id": 12,
        "name": "Autocare",
        "subdominio": "autocare",
        "logo_url": "https://cdn.example/autocare.png",
        "logo_url_dark": None,
        "color_primario": "#FF0000",
        "color_secundario": "#00FF00",
        "mostrar_marca_mukusoft": False,
    }


def test_login_falls_back_to_minimal_tenant_when_repo_omits_it(monkeypatch):
    """Si el repo no devuelve `tenant`, el endpoint arma uno con id+name."""

    def fake_login(username, password, *, subdominio=None, host=None):
        return (
            {
                "id": 1,
                "name": username,
                "role": "operador",
                "lavanderia_id": 5,
                "lavanderia_name": "Mini",
            },
            ["dashboard"],
        )

    monkeypatch.setattr("backend.api.routers.auth.authenticate_user", fake_login)

    response = _client(monkeypatch).post(
        "/auth/login",
        json={"username": "u", "password": "p", "subdominio": "mini"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tenant"] == {
        "id": 5,
        "name": "Mini",
        "subdominio": None,
        "logo_url": None,
        "logo_url_dark": None,
        "color_primario": None,
        "color_secundario": None,
        "mostrar_marca_mukusoft": True,
    }


def test_login_maps_tenant_errors_to_bad_request(monkeypatch):
    def fake_login(*args, **kwargs):
        raise ValueError("La lavanderia indicada no existe.")

    monkeypatch.setattr("backend.api.routers.auth.authenticate_user", fake_login)

    response = _client(monkeypatch).post(
        "/auth/login",
        json={"username": "admin", "password": "secret", "subdominio": "nope"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "La lavanderia indicada no existe."}


def test_catalog_services_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.get_active_services",
        lambda lavanderia_id=None: [
            {
                "id": 1,
                "name": "Lavado",
                "price": 50000,
                "is_active": 1,
                "created_at": None,
                "lavanderia_id": lavanderia_id,
            }
        ],
    )

    response = _client(monkeypatch).get(
        "/catalogs/services?lavanderia_id=999",
        headers=_auth_headers("register_sale", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Lavado",
            "price": 50000.0,
            "is_active": True,
            "created_at": None,
            "lavanderia_id": 3,
        }
    ]


def test_catalog_services_endpoint_can_include_inactive(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.get_all_services",
        lambda lavanderia_id=None: [
            {
                "id": 1,
                "name": "Lavado",
                "price": 50000,
                "is_active": 0,
                "created_at": None,
                "lavanderia_id": lavanderia_id,
            }
        ],
    )

    response = _client(monkeypatch).get(
        "/catalogs/services?only_active=false",
        headers=_auth_headers("settings", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json()[0]["is_active"] is False


def test_create_catalog_service_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.add_service",
        lambda name, lavanderia_id=None, price=0: 12,
    )

    response = _client(monkeypatch).post(
        "/catalogs/services",
        headers=_auth_headers("settings", lavanderia_id=3),
        json={"name": "Lavado premium", "price": 35000},
    )

    assert response.status_code == 201
    assert response.json() == {"id": 12}


def test_update_catalog_service_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.rename_service",
        lambda service_id, name, lavanderia_id=None, price=None: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.catalogs.get_service_by_id",
        lambda service_id, lavanderia_id=None: {
            "id": service_id,
            "name": "Lavado premium",
            "price": 35000,
            "is_active": 1,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
        },
    )

    response = _client(monkeypatch).put(
        "/catalogs/services/12",
        headers=_auth_headers("settings", lavanderia_id=3),
        json={"name": "Lavado premium", "price": 35000},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 12
    assert response.json()["price"] == 35000.0


def test_toggle_catalog_service_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.toggle_service_status",
        lambda service_id, lavanderia_id=None: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.catalogs.get_service_by_id",
        lambda service_id, lavanderia_id=None: {
            "id": service_id,
            "name": "Lavado premium",
            "price": 35000,
            "is_active": 0,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
        },
    )

    response = _client(monkeypatch).patch(
        "/catalogs/services/12/status",
        headers=_auth_headers("settings", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json() == {"id": 12, "is_active": False}


def test_delete_catalog_service_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.remove_service",
        lambda service_id, lavanderia_id=None: None,
    )

    response = _client(monkeypatch).delete(
        "/catalogs/services/12",
        headers=_auth_headers("settings", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Servicio eliminado."}


def test_create_catalog_product_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.add_product",
        lambda name, lavanderia_id=None, price=0: 21,
    )

    response = _client(monkeypatch).post(
        "/catalogs/products",
        headers=_auth_headers("settings", lavanderia_id=3),
        json={"name": "Shampoo", "price": 12000},
    )

    assert response.status_code == 201
    assert response.json() == {"id": 21}


def test_create_expense_category_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.add_category",
        lambda name, lavanderia_id=None: 31,
    )

    response = _client(monkeypatch).post(
        "/catalogs/expense-categories",
        headers=_auth_headers("settings", lavanderia_id=3),
        json={"name": "Insumos"},
    )

    assert response.status_code == 201
    assert response.json() == {"id": 31}


def test_create_vehicle_type_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.catalogs.add_vehicle_type",
        lambda name, lavanderia_id=None: 41,
    )

    response = _client(monkeypatch).post(
        "/catalogs/vehicle-types",
        headers=_auth_headers("settings", lavanderia_id=3),
        json={"name": "Camioneta"},
    )

    assert response.status_code == 201
    assert response.json() == {"id": 41}


def test_list_clients_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.clients.get_clients",
        lambda lavanderia_id, only_active=False: [
            {
                "id": 2,
                "name": "Ana",
                "client_type": "particular",
                "ruc_ci": None,
                "phone": "0981000000",
                "email": None,
                "is_active": True,
                "created_at": None,
                "lavanderia_id": lavanderia_id,
            }
        ],
    )

    response = _client(monkeypatch).get(
        "/clients?only_active=true",
        headers=_auth_headers("register_sale", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json() == [
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


def test_find_client_by_ruc_ci_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.clients.find_client_by_ruc_ci",
        lambda lavanderia_id, ruc_ci: {
            "id": 8,
            "name": "Acme SA",
            "client_type": "empresa",
            "ruc_ci": ruc_ci,
            "phone": None,
            "email": "facturas@acme.com",
            "is_active": True,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
        },
    )

    response = _client(monkeypatch).get(
        "/clients/by-ruc-ci/80012345-6",
        headers=_auth_headers("register_sale", lavanderia_id=5),
    )

    assert response.status_code == 200
    assert response.json()["ruc_ci"] == "80012345-6"
    assert response.json()["lavanderia_id"] == 5


def test_create_client_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.clients.register_client",
        lambda lavanderia_id, nombre, tipo_cliente, ruc_ci=None, telefono=None, email=None: 77,
    )

    response = _client(monkeypatch).post(
        "/clients",
        headers=_auth_headers("settings", lavanderia_id=4),
        json={
            "name": "Acme SA",
            "client_type": "empresa",
            "ruc_ci": "80012345-6",
            "phone": "0981000000",
            "email": "facturas@acme.com",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"id": 77}


def test_update_client_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.clients.edit_client",
        lambda lavanderia_id, client_id, nombre, tipo_cliente, ruc_ci=None, telefono=None, email=None: client_id,
    )
    monkeypatch.setattr(
        "backend.api.routers.clients.get_client",
        lambda lavanderia_id, client_id: {
            "id": client_id,
            "name": "Acme SA",
            "client_type": "empresa",
            "ruc_ci": "80012345-6",
            "phone": "0981000000",
            "email": "facturas@acme.com",
            "is_active": True,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
        },
    )

    response = _client(monkeypatch).put(
        "/clients/9",
        headers=_auth_headers("settings", lavanderia_id=4),
        json={
            "name": "Acme SA",
            "client_type": "empresa",
            "ruc_ci": "80012345-6",
            "phone": "0981000000",
            "email": "facturas@acme.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 9
    assert response.json()["lavanderia_id"] == 4


def test_toggle_client_status_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.clients.toggle_client_status",
        lambda lavanderia_id, client_id: client_id,
    )
    monkeypatch.setattr(
        "backend.api.routers.clients.get_client",
        lambda lavanderia_id, client_id: {
            "id": client_id,
            "name": "Acme SA",
            "client_type": "empresa",
            "ruc_ci": "80012345-6",
            "phone": None,
            "email": None,
            "is_active": False,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
        },
    )

    response = _client(monkeypatch).patch(
        "/clients/9/status",
        headers=_auth_headers("settings", lavanderia_id=4),
    )

    assert response.status_code == 200
    assert response.json()["id"] == 9
    assert response.json()["is_active"] is False


def test_create_sale_endpoint(monkeypatch):
    calls = {}

    def fake_register_sale(**kwargs):
        calls.update(kwargs)
        return 44

    monkeypatch.setattr("backend.api.routers.sales.register_sale", fake_register_sale)

    response = _client(monkeypatch).post(
        "/sales",
        headers=_auth_headers("register_sale", user_id=2, lavanderia_id=9),
        json={
            "usuario_id": 2,
            "fecha_venta": "2026-05-01",
            "tipo_cobro": "Contado",
            "items": [{"servicio_id": 5, "cantidad": 1}],
        },
    )

    assert response.status_code == 201
    assert response.json() == {"id": 44}
    assert calls["lavanderia_id"] == 9
    assert calls["usuario_id"] == 2
    assert calls["items"] == [{"servicio_id": 5, "cantidad": 1}]


def test_sales_list_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.sales.get_sales_export_rows",
        lambda start_date=None, end_date=None, lavanderia_id=None: [
            {
                "sale_id": 10,
                "date": "2026-05-01",
                "payment_type": "Contado",
                "payment_method": "Efectivo",
                "requires_invoice": False,
                "customer_name": "Consumidor Final",
                "ruc_ci": None,
                "license_plate": "ABC123",
                "vehicle_type": "Auto",
                "item_type": "Servicio",
                "item": "Lavado",
                "quantity": 1,
                "unit_price": 50000,
                "subtotal": 50000,
                "sale_total": 50000,
                "created_by": "admin",
                "notes": None,
            }
        ],
    )

    response = _client(monkeypatch).get(
        "/sales?start_date=2026-05-01&end_date=2026-05-31",
        headers=_auth_headers("movements", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json()[0]["sale_id"] == 10
    assert response.json()[0]["subtotal"] == 50000.0


def test_sales_grouped_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.sales.get_sales_grouped",
        lambda start_date=None, end_date=None, lavanderia_id=None: [
            {
                "id": 10,
                "date": "2026-05-01",
                "created_at": None,
                "payment_type": "Contado",
                "payment_method": "Efectivo",
                "requires_invoice": False,
                "total": 62000,
                "notes": "Cliente frecuente",
                "customer_id": 4,
                "customer_name": "Ana",
                "ruc_ci": None,
                "vehicle_id": 9,
                "license_plate": "ABC123",
                "vehicle_type_id": 1,
                "vehicle_type_name": "Auto",
                "created_by_user_id": 2,
                "created_by": "admin",
                "lavanderia_id": lavanderia_id,
                "items": [
                    {
                        "id": 100,
                        "item_type": "Servicio",
                        "item_name": "Lavado",
                        "service_id": 5,
                        "product_id": None,
                        "quantity": 1,
                        "unit_price": 50000,
                        "subtotal": 50000,
                    },
                    {
                        "id": 101,
                        "item_type": "Producto",
                        "item_name": "Cera",
                        "service_id": None,
                        "product_id": 7,
                        "quantity": 1,
                        "unit_price": 12000,
                        "subtotal": 12000,
                    },
                ],
            }
        ],
    )

    response = _client(monkeypatch).get(
        "/sales/grouped?start_date=2026-05-01&end_date=2026-05-31",
        headers=_auth_headers("movements", lavanderia_id=3),
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == 10
    assert body[0]["items"][0]["item_type"] == "Servicio"
    assert body[0]["items"][1]["item_name"] == "Cera"
    assert body[0]["lavanderia_id"] == 3


def test_sale_detail_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.sales.get_grouped_sale_by_id",
        lambda sale_id, lavanderia_id=None: {
            "id": sale_id,
            "date": "2026-05-01",
            "created_at": None,
            "payment_type": "Contado",
            "payment_method": "Efectivo",
            "requires_invoice": False,
            "total": 50000,
            "notes": None,
            "customer_id": 4,
            "customer_name": "Ana",
            "ruc_ci": None,
            "vehicle_id": 9,
            "license_plate": "ABC123",
            "vehicle_type_id": 1,
            "vehicle_type_name": "Auto",
            "created_by_user_id": 2,
            "created_by": "admin",
            "lavanderia_id": lavanderia_id,
            "items": [
                {
                    "id": 100,
                    "item_type": "Servicio",
                    "item_name": "Lavado",
                    "service_id": 5,
                    "product_id": None,
                    "quantity": 1,
                    "unit_price": 50000,
                    "subtotal": 50000,
                }
            ],
        },
    )

    response = _client(monkeypatch).get(
        "/sales/10",
        headers=_auth_headers("movements", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert response.json()["items"][0]["item_name"] == "Lavado"


def test_sale_detail_endpoint_returns_not_found(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.sales.get_grouped_sale_by_id",
        lambda sale_id, lavanderia_id=None: None,
    )

    response = _client(monkeypatch).get(
        "/sales/99",
        headers=_auth_headers("movements", lavanderia_id=3),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "La venta indicada no existe en esta lavanderia."}


def test_create_expense_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.expenses.register_expense",
        lambda *args, **kwargs: 88,
    )

    response = _client(monkeypatch).post(
        "/expenses",
        headers=_auth_headers("register_expense", user_id=2, lavanderia_id=3),
        json={
            "usuario_id": 2,
            "fecha": "2026-05-01",
            "categoria_egreso_id": 4,
            "monto": 25000,
            "descripcion": "Insumos",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"id": 88}


def test_expense_detail_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.expenses.get_expense",
        lambda expense_id, lavanderia_id=None: {
            "id": expense_id,
            "date": "2026-05-01",
            "category_id": 4,
            "category": "Insumos",
            "amount": 25000,
            "description": "Compra",
            "created_by": "admin",
            "user_id": 2,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
            "estado": True,
        },
    )

    response = _client(monkeypatch).get(
        "/expenses/88",
        headers=_auth_headers("movements", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json()["id"] == 88
    assert response.json()["category"] == "Insumos"


def test_update_expense_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.expenses.edit_expense",
        lambda *args, **kwargs: kwargs["expense_id"],
    )
    monkeypatch.setattr(
        "backend.api.routers.expenses.get_expense",
        lambda expense_id, lavanderia_id=None: {
            "id": expense_id,
            "date": "2026-05-02",
            "category_id": 4,
            "category": "Insumos",
            "amount": 32000,
            "description": "Actualizado",
            "created_by": "admin",
            "user_id": 2,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
            "estado": True,
        },
    )

    response = _client(monkeypatch).put(
        "/expenses/88",
        headers=_auth_headers("register_expense", user_id=2, lavanderia_id=3),
        json={
            "usuario_id": 2,
            "fecha": "2026-05-02",
            "categoria_egreso_id": 4,
            "monto": 32000,
            "descripcion": "Actualizado",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 88
    assert response.json()["amount"] == 32000.0


def test_update_expense_rejects_other_user_id(monkeypatch):
    response = _client(monkeypatch).put(
        "/expenses/88",
        headers=_auth_headers("register_expense", user_id=2, lavanderia_id=3),
        json={
            "usuario_id": 5,
            "fecha": "2026-05-02",
            "categoria_egreso_id": 4,
            "monto": 32000,
            "descripcion": "Actualizado",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "No puede editar egresos en nombre de otro usuario."
    }


def test_cancel_expense_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.expenses.remove_expense",
        lambda *args, **kwargs: None,
    )

    response = _client(monkeypatch).delete(
        "/expenses/88",
        headers=_auth_headers("register_expense", user_id=2, lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Egreso anulado."}


def test_cancel_expense_returns_conflict_when_already_cancelled(monkeypatch):
    def fake_remove_expense(*args, **kwargs):
        raise ValueError("El egreso indicado ya fue anulado.")

    monkeypatch.setattr("backend.api.routers.expenses.remove_expense", fake_remove_expense)

    response = _client(monkeypatch).delete(
        "/expenses/88",
        headers=_auth_headers("register_expense", user_id=2, lavanderia_id=3),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "El egreso indicado ya fue anulado."}


def test_update_sale_endpoint(monkeypatch):
    calls = {}

    def fake_edit_sale(**kwargs):
        calls.update(kwargs)
        return kwargs["sale_id"]

    monkeypatch.setattr("backend.api.routers.sales.edit_sale", fake_edit_sale)
    monkeypatch.setattr(
        "backend.api.routers.sales.get_grouped_sale_by_id",
        lambda sale_id, lavanderia_id=None: {
            "id": sale_id,
            "date": "2026-05-01",
            "created_at": None,
            "payment_type": "Credito",
            "payment_method": "Transferencia",
            "requires_invoice": False,
            "total": 50000,
            "notes": "Actualizada",
            "customer_id": 4,
            "customer_name": "Ana",
            "ruc_ci": None,
            "vehicle_id": 9,
            "license_plate": "ABC123",
            "vehicle_type_id": 1,
            "vehicle_type_name": "Auto",
            "created_by_user_id": 2,
            "created_by": "admin",
            "lavanderia_id": lavanderia_id,
            "items": [
                {
                    "id": 100,
                    "item_type": "Servicio",
                    "item_name": "Lavado",
                    "service_id": 5,
                    "product_id": None,
                    "quantity": 1,
                    "unit_price": 50000,
                    "subtotal": 50000,
                }
            ],
        },
    )

    response = _client(monkeypatch).put(
        "/sales/44",
        headers=_auth_headers("edit_sale", user_id=2, lavanderia_id=9),
        json={
            "usuario_id": 2,
            "fecha_venta": "2026-05-01",
            "tipo_cobro": "Credito",
            "metodo_pago": "Transferencia",
            "observacion": "Actualizada",
            "items": [{"servicio_id": 5, "cantidad": 1}],
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 44
    assert calls["lavanderia_id"] == 9
    assert calls["usuario_id"] == 2
    assert calls["sale_id"] == 44


def test_update_sale_rejects_other_user_id(monkeypatch):
    response = _client(monkeypatch).put(
        "/sales/44",
        headers=_auth_headers("edit_sale", user_id=2, lavanderia_id=9),
        json={
            "usuario_id": 5,
            "fecha_venta": "2026-05-01",
            "tipo_cobro": "Contado",
            "items": [{"servicio_id": 5, "cantidad": 1}],
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "No puede editar ventas en nombre de otro usuario."
    }


def test_vehicle_by_plate_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.vehicles.find_vehicle_by_plate",
        lambda license_plate, lavanderia_id=None: {
            "id": 7,
            "license_plate": license_plate,
            "vehicle_type_id": 1,
            "vehicle_type_name": "Auto",
            "owner_name": "Ana",
            "phone": None,
            "client_id": 2,
            "is_active": 1,
            "created_at": None,
            "lavanderia_id": lavanderia_id,
        },
    )

    response = _client(monkeypatch).get(
        "/vehicles/by-plate/abc123",
        headers=_auth_headers("register_sale", lavanderia_id=5),
    )

    assert response.status_code == 200
    assert response.json()["license_plate"] == "abc123"
    assert response.json()["lavanderia_id"] == 5


def test_sales_summary_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.reports.get_sales_summary",
        lambda start_date, end_date, lavanderia_id=None: {
            "start_date": start_date,
            "end_date": end_date,
            "sales_total": 100000,
            "expense_total": 25000,
            "net_balance": 75000,
            "service_count": 2,
            "service_sales_total": 80000,
            "product_count": 1,
            "sales_breakdown": [{"name": "Lavado", "count": 2, "total": 80000}],
            "expense_breakdown": [{"name": "Insumos", "total": 25000}],
            "payment_breakdown": {"contado": 100000, "credito": 0},
        },
    )

    response = _client(monkeypatch).get(
        "/reports/sales-summary?start_date=2026-05-01&end_date=2026-05-31",
        headers=_auth_headers("export", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json()["net_balance"] == 75000.0


def test_protected_endpoint_requires_token(monkeypatch):
    response = _client(monkeypatch).get(
        "/sales?start_date=2026-05-01&end_date=2026-05-31"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Hace falta un token Bearer."}


def test_protected_endpoint_rejects_missing_permission(monkeypatch):
    response = _client(monkeypatch).get(
        "/reports/sales-summary?start_date=2026-05-01&end_date=2026-05-31",
        headers=_auth_headers("movements", lavanderia_id=3),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "No tiene permiso para esta accion."}


def test_protected_endpoint_rejects_host_tenant_mismatch(monkeypatch):
    monkeypatch.setattr(
        "backend.api.deps.get_tenant_by_host",
        lambda host: SimpleNamespace(id=99),
    )

    response = _client(monkeypatch).get(
        "/catalogs/services",
        headers={
            **_auth_headers("register_sale", lavanderia_id=3),
            "Host": "demo.mukusoft.com",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "El token no pertenece al tenant del host."}


def test_create_sale_rejects_other_user_id(monkeypatch):
    response = _client(monkeypatch).post(
        "/sales",
        headers=_auth_headers("register_sale", user_id=2, lavanderia_id=9),
        json={
            "usuario_id": 5,
            "fecha_venta": "2026-05-01",
            "tipo_cobro": "Contado",
            "items": [{"servicio_id": 5, "cantidad": 1}],
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "No puede registrar ventas en nombre de otro usuario."
    }


# --- void sale ---

def test_void_sale_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.sales.remove_sale",
        lambda lavanderia_id, sale_id: None,
    )

    response = _client(monkeypatch).delete(
        "/sales/10",
        headers=_auth_headers("manage_sales", lavanderia_id=3),
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Venta anulada."}


def test_void_sale_not_found(monkeypatch):
    def raise_not_found(lavanderia_id, sale_id):
        raise ValueError("La venta indicada no existe en esta lavanderia.")

    monkeypatch.setattr("backend.api.routers.sales.remove_sale", raise_not_found)

    response = _client(monkeypatch).delete(
        "/sales/99",
        headers=_auth_headers("manage_sales", lavanderia_id=3),
    )

    assert response.status_code == 404


def test_void_sale_already_voided_returns_conflict(monkeypatch):
    def raise_conflict(lavanderia_id, sale_id):
        raise ValueError("La venta ya fue anulada.")

    monkeypatch.setattr("backend.api.routers.sales.remove_sale", raise_conflict)

    response = _client(monkeypatch).delete(
        "/sales/10",
        headers=_auth_headers("manage_sales", lavanderia_id=3),
    )

    assert response.status_code == 409
    assert "anulada" in response.json()["detail"]


def test_update_voided_sale_returns_conflict(monkeypatch):
    def raise_conflict(**kwargs):
        raise ValueError("No se puede editar una venta que ya fue anulada.")

    monkeypatch.setattr("backend.api.routers.sales.edit_sale", raise_conflict)

    response = _client(monkeypatch).put(
        "/sales/10",
        headers=_auth_headers("edit_sale", lavanderia_id=3),
        json={
            "fecha_venta": "2026-05-01",
            "tipo_cobro": "Contado",
            "items": [{"servicio_id": 5, "cantidad": 1}],
        },
    )

    assert response.status_code == 409
    assert "anulada" in response.json()["detail"]


# --- vehicles ---

_VEHICLE = {
    "id": 7,
    "license_plate": "ABC123",
    "vehicle_type_id": 1,
    "vehicle_type_name": "Auto",
    "owner_name": "Ana",
    "phone": "0981000000",
    "client_id": 2,
    "is_active": 1,
    "created_at": None,
    "lavanderia_id": 5,
}


def test_list_vehicles_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.vehicles.list_vehicles",
        lambda lavanderia_id, only_active, search: [_VEHICLE],
    )

    response = _client(monkeypatch).get(
        "/vehicles",
        headers=_auth_headers("register_sale", lavanderia_id=5),
    )

    assert response.status_code == 200
    assert response.json()[0]["license_plate"] == "ABC123"


def test_list_vehicles_only_active_false(monkeypatch):
    received = {}

    def fake_list(lavanderia_id, only_active, search):
        received["only_active"] = only_active
        return [_VEHICLE]

    monkeypatch.setattr("backend.api.routers.vehicles.list_vehicles", fake_list)

    _client(monkeypatch).get(
        "/vehicles?only_active=false",
        headers=_auth_headers("settings", lavanderia_id=5),
    )

    assert received["only_active"] is False


def test_get_vehicle_detail_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.vehicles.get_vehicle",
        lambda vehicle_id, lavanderia_id: _VEHICLE,
    )

    response = _client(monkeypatch).get(
        "/vehicles/7",
        headers=_auth_headers("register_sale", lavanderia_id=5),
    )

    assert response.status_code == 200
    assert response.json()["id"] == 7


def test_get_vehicle_detail_not_found(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.vehicles.get_vehicle",
        lambda vehicle_id, lavanderia_id: None,
    )

    response = _client(monkeypatch).get(
        "/vehicles/99",
        headers=_auth_headers("register_sale", lavanderia_id=5),
    )

    assert response.status_code == 404


def test_update_vehicle_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.vehicles.edit_vehicle",
        lambda vehicle_id, vehicle_type_id, owner_name, phone, lavanderia_id: vehicle_id,
    )
    monkeypatch.setattr(
        "backend.api.routers.vehicles.get_vehicle",
        lambda vehicle_id, lavanderia_id: _VEHICLE,
    )

    response = _client(monkeypatch).put(
        "/vehicles/7",
        headers=_auth_headers("settings", lavanderia_id=5),
        json={"vehicle_type_id": 1, "owner_name": "Ana", "phone": "0981000000"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 7


def test_update_vehicle_not_found(monkeypatch):
    def raise_not_found(*args, **kwargs):
        raise ValueError("El vehiculo indicado no existe.")

    monkeypatch.setattr("backend.api.routers.vehicles.edit_vehicle", raise_not_found)

    response = _client(monkeypatch).put(
        "/vehicles/99",
        headers=_auth_headers("settings", lavanderia_id=5),
        json={"vehicle_type_id": 1},
    )

    assert response.status_code == 404


def test_set_vehicle_status_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.vehicles.toggle_vehicle_status",
        lambda vehicle_id, active, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.vehicles.get_vehicle",
        lambda vehicle_id, lavanderia_id: {**_VEHICLE, "is_active": 0},
    )

    response = _client(monkeypatch).patch(
        "/vehicles/7/status",
        headers=_auth_headers("settings", lavanderia_id=5),
        json={"active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_set_vehicle_status_not_found(monkeypatch):
    def raise_not_found(*args, **kwargs):
        raise ValueError("El vehiculo indicado no existe.")

    monkeypatch.setattr("backend.api.routers.vehicles.toggle_vehicle_status", raise_not_found)

    response = _client(monkeypatch).patch(
        "/vehicles/99/status",
        headers=_auth_headers("settings", lavanderia_id=5),
        json={"active": True},
    )

    assert response.status_code == 404
