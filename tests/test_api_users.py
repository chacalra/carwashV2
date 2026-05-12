"""Tests para /users."""

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.utils.security import create_access_token


def _client(monkeypatch, *, user_id=7, role="admin"):
    monkeypatch.setattr(
        "backend.api.deps.get_user_by_id",
        lambda uid, lavanderia_id=None: {
            "id": uid,
            "name": f"user-{uid}",
            "role": role,
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


# ---------- list ----------


def test_list_users(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.users.get_all_users",
        lambda lavanderia_id: [
            {
                "id": 1,
                "name": "admin",
                "role": "admin",
                "role_id": 1,
                "is_active": 1,
                "created_at": None,
            },
            {
                "id": 2,
                "name": "ana",
                "role": "operario",
                "role_id": 2,
                "is_active": 0,
                "created_at": None,
            },
        ],
    )
    response = _client(monkeypatch).get(
        "/users",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["username"] == "admin"
    assert body[1]["is_active"] is False


def test_list_users_requires_settings(monkeypatch):
    response = _client(monkeypatch).get(
        "/users",
        headers=_auth_headers("dashboard"),
    )
    assert response.status_code == 403


# ---------- create ----------


def test_create_user_ok(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_name",
        lambda name, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "operario", "is_active": 1},
    )

    def fake_create(name, password_hash, lavanderia_id, role_id):
        captured.update(
            {"name": name, "lavanderia_id": lavanderia_id, "role_id": role_id}
        )
        captured["password_hash_provided"] = bool(password_hash)
        return 42

    monkeypatch.setattr("backend.api.routers.users.create_user", fake_create)

    response = _client(monkeypatch).post(
        "/users",
        headers=_auth_headers("settings"),
        json={"username": "ana", "role_id": 2, "password": "abc123"},
    )
    assert response.status_code == 201
    assert response.json() == {"id": 42}
    assert captured["password_hash_provided"] is True
    assert captured["name"] == "ana"
    assert captured["role_id"] == 2


def test_create_user_password_too_short(monkeypatch):
    response = _client(monkeypatch).post(
        "/users",
        headers=_auth_headers("settings"),
        json={"username": "ana", "role_id": 2, "password": "12345"},
    )
    assert response.status_code == 422


def test_create_user_conflict_when_name_exists(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_name",
        lambda name, lavanderia_id: {
            "id": 5,
            "name": name,
            "role": "x",
            "role_id": 1,
            "is_active": 1,
        },
    )
    response = _client(monkeypatch).post(
        "/users",
        headers=_auth_headers("settings"),
        json={"username": "admin", "role_id": 2, "password": "abc123"},
    )
    assert response.status_code == 409


def test_create_user_invalid_role(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_name",
        lambda name, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_role_by_id",
        lambda role_id, lavanderia_id: None,
    )
    response = _client(monkeypatch).post(
        "/users",
        headers=_auth_headers("settings"),
        json={"username": "ana", "role_id": 999, "password": "abc123"},
    )
    assert response.status_code == 400


# ---------- edit ----------


def test_edit_user_blocks_self(monkeypatch):
    """No podés editarte a vos mismo."""
    response = _client(monkeypatch, user_id=7).put(
        "/users/7",
        headers=_auth_headers("settings", user_id=7),
        json={"username": "newname", "role_id": 1},
    )
    assert response.status_code == 403


def test_edit_user_ok(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_id",
        lambda user_id, lavanderia_id: {
            "id": user_id,
            "name": "old",
            "role": "operario",
            "role_id": 2,
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "admin", "is_active": 1},
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_name",
        lambda name, lavanderia_id: None,
    )
    # El nuevo rol tiene `settings`, así que el guard de "último admin"
    # ni siquiera consulta count_settings_admins.
    monkeypatch.setattr(
        "backend.api.routers.users.get_permissions_for_role",
        lambda role_id, lavanderia_id: ["settings", "register_sale"],
    )

    def fake_update(user_id, name, lavanderia_id, role_id):
        captured.update(
            {"user_id": user_id, "name": name, "role_id": role_id}
        )

    monkeypatch.setattr("backend.api.routers.users.update_user", fake_update)

    response = _client(monkeypatch, user_id=7).put(
        "/users/8",
        headers=_auth_headers("settings", user_id=7),
        json={"username": "ana_nueva", "role_id": 1},
    )
    assert response.status_code == 200
    assert captured == {"user_id": 8, "name": "ana_nueva", "role_id": 1}


# ---------- toggle ----------


def test_toggle_user_blocks_self(monkeypatch):
    response = _client(monkeypatch, user_id=7).patch(
        "/users/7/status",
        headers=_auth_headers("settings", user_id=7),
    )
    assert response.status_code == 403


def test_toggle_user_ok(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_id",
        lambda user_id, lavanderia_id: {
            "id": user_id,
            "name": "ana",
            "role": "operario",
            "role_id": 2,
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.users.toggle_user",
        lambda user_id, lavanderia_id: None,
    )
    # Hay otros admins, el guard pasa.
    monkeypatch.setattr(
        "backend.api.routers.users.count_settings_admins",
        lambda lavanderia_id, **kw: 2,
    )
    response = _client(monkeypatch, user_id=7).patch(
        "/users/8/status",
        headers=_auth_headers("settings", user_id=7),
    )
    assert response.status_code == 200


# ---------- password ----------


def test_password_blocks_self(monkeypatch):
    response = _client(monkeypatch, user_id=7).patch(
        "/users/7/password",
        headers=_auth_headers("settings", user_id=7),
        json={"password": "abc123"},
    )
    assert response.status_code == 403


def test_password_ok_for_other_user(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_id",
        lambda user_id, lavanderia_id: {
            "id": user_id,
            "name": "ana",
            "role": "operario",
            "role_id": 2,
            "is_active": 1,
        },
    )

    def fake_update(user_id, password_hash, lavanderia_id):
        captured.update({"user_id": user_id, "lavanderia_id": lavanderia_id})
        captured["had_hash"] = bool(password_hash)

    monkeypatch.setattr(
        "backend.api.routers.users.update_user_password",
        fake_update,
    )
    response = _client(monkeypatch, user_id=7).patch(
        "/users/8/password",
        headers=_auth_headers("settings", user_id=7),
        json={"password": "newpass"},
    )
    assert response.status_code == 200
    assert captured == {"user_id": 8, "lavanderia_id": 3, "had_hash": True}


def test_password_too_short(monkeypatch):
    response = _client(monkeypatch, user_id=7).patch(
        "/users/8/password",
        headers=_auth_headers("settings", user_id=7),
        json={"password": "12"},
    )
    assert response.status_code == 422


# ---------- guard: último admin ----------


def test_toggle_user_blocks_when_last_admin(monkeypatch):
    """Desactivar al único admin del tenant debe fallar 400."""
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_id",
        lambda user_id, lavanderia_id: {
            "id": user_id,
            "name": "boss",
            "role": "admin",
            "role_id": 1,
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.users.count_settings_admins",
        lambda lavanderia_id, **kw: 0,
    )
    response = _client(monkeypatch, user_id=7).patch(
        "/users/8/status",
        headers=_auth_headers("settings", user_id=7),
    )
    assert response.status_code == 400
    assert "último administrador" in response.json()["detail"]


def test_edit_user_blocks_role_change_to_non_admin_when_last(monkeypatch):
    """Cambiar el rol del último admin a uno sin settings debe fallar."""
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_id",
        lambda user_id, lavanderia_id: {
            "id": user_id,
            "name": "boss",
            "role": "admin",
            "role_id": 1,
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_role_by_id",
        lambda role_id, lavanderia_id: {
            "id": role_id,
            "name": "operario",
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_user_by_name",
        lambda name, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.users.get_permissions_for_role",
        lambda role_id, lavanderia_id: ["register_sale"],  # sin settings
    )
    monkeypatch.setattr(
        "backend.api.routers.users.count_settings_admins",
        lambda lavanderia_id, **kw: 0,
    )
    response = _client(monkeypatch, user_id=7).put(
        "/users/8",
        headers=_auth_headers("settings", user_id=7),
        json={"username": "boss", "role_id": 2},
    )
    assert response.status_code == 400
    assert "último administrador" in response.json()["detail"]
