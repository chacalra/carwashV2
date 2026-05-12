"""Tests para /permissions y /roles."""

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.utils.security import create_access_token


def _client(monkeypatch, *, current_user_role="admin"):
    """TestClient con get_user_by_id stubeado para autenticar el bearer."""
    monkeypatch.setattr(
        "backend.api.deps.get_user_by_id",
        lambda user_id, lavanderia_id=None: {
            "id": user_id,
            "name": f"user-{user_id}",
            "role": current_user_role,
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


# ---------- /permissions ----------


def test_permissions_requires_settings(monkeypatch):
    response = _client(monkeypatch).get(
        "/permissions",
        headers=_auth_headers("dashboard"),
    )
    assert response.status_code == 403


def test_permissions_lists_all_codes(monkeypatch):
    response = _client(monkeypatch).get(
        "/permissions",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 200
    body = response.json()
    codes = {item["code"] for item in body}
    assert {"dashboard", "settings", "register_sale", "movements"}.issubset(codes)
    # Cada item tiene code + label
    for item in body:
        assert "code" in item and "label" in item


# ---------- /roles GET / POST ----------


def test_list_roles_includes_permission_count(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_all_roles",
        lambda lavanderia_id: [
            {"id": 1, "name": "admin", "is_active": 1},
            {"id": 2, "name": "operario", "is_active": 0},
        ],
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.get_permission_counts",
        lambda lavanderia_id: {1: 8, 2: 1},
    )
    response = _client(monkeypatch).get(
        "/roles",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "admin", "is_active": True, "permission_count": 8},
        {"id": 2, "name": "operario", "is_active": False, "permission_count": 1},
    ]


def test_create_role_returns_id(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_name",
        lambda name, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.create_role",
        lambda name, lavanderia_id: 99,
    )
    response = _client(monkeypatch).post(
        "/roles",
        headers=_auth_headers("settings"),
        json={"name": "supervisor"},
    )
    assert response.status_code == 201
    assert response.json() == {"id": 99}


def test_create_role_conflict_when_name_exists(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_name",
        lambda name, lavanderia_id: {"id": 1, "name": name, "is_active": 1},
    )
    response = _client(monkeypatch).post(
        "/roles",
        headers=_auth_headers("settings"),
        json={"name": "admin"},
    )
    assert response.status_code == 409


# ---------- rename / toggle ----------


def test_rename_role_404_if_not_found(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: None,
    )
    response = _client(monkeypatch).put(
        "/roles/123",
        headers=_auth_headers("settings"),
        json={"name": "x"},
    )
    assert response.status_code == 404


def test_rename_role_conflict_if_target_name_taken(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "old", "is_active": 1},
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_name",
        lambda name, lavanderia_id: {"id": 999, "name": name, "is_active": 1},
    )
    response = _client(monkeypatch).put(
        "/roles/1",
        headers=_auth_headers("settings"),
        json={"name": "operario"},
    )
    assert response.status_code == 409


def test_rename_role_ok(monkeypatch):
    called = {}
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "old", "is_active": 1},
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_name",
        lambda name, lavanderia_id: None,
    )

    def fake_rename(role_id, name, lavanderia_id):
        called.update({"role_id": role_id, "name": name, "lavanderia_id": lavanderia_id})

    monkeypatch.setattr("backend.api.routers.roles.rename_role", fake_rename)

    response = _client(monkeypatch).put(
        "/roles/5",
        headers=_auth_headers("settings"),
        json={"name": "supervisor"},
    )
    assert response.status_code == 200
    assert called == {"role_id": 5, "name": "supervisor", "lavanderia_id": 3}


def test_toggle_role_blocks_self_role(monkeypatch):
    """No podés desactivar el rol al que vos pertenecés."""
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "admin", "is_active": 1},
    )
    response = _client(monkeypatch, current_user_role="admin").patch(
        "/roles/1/status",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 400
    assert "tu propio rol" in response.json()["detail"]


def test_toggle_role_ok_for_other_role(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "operario", "is_active": 1},
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.toggle_role",
        lambda role_id, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.count_settings_admins",
        lambda lavanderia_id, **kw: 1,
    )
    response = _client(monkeypatch, current_user_role="admin").patch(
        "/roles/2/status",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 200


# ---------- permissions per role ----------


def test_get_role_permissions(monkeypatch):
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "admin", "is_active": 1},
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.get_permissions_for_role",
        lambda role_ref, lavanderia_id: ["dashboard", "settings"],
    )
    response = _client(monkeypatch).get(
        "/roles/1/permissions",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 200
    assert response.json() == ["dashboard", "settings"]


def test_replace_role_permissions_self_role_cannot_drop_settings(monkeypatch):
    """Si edito mi propio rol, no puedo sacarme `settings`."""
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "admin", "is_active": 1},
    )
    response = _client(monkeypatch, current_user_role="admin").put(
        "/roles/1/permissions",
        headers=_auth_headers("settings"),
        json={"permissions": ["dashboard", "register_sale"]},
    )
    assert response.status_code == 400
    assert "settings" in response.json()["detail"]


def test_replace_role_permissions_ok(monkeypatch):
    payload = {}
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {"id": role_id, "name": "operario", "is_active": 1},
    )

    def fake_set(role_ref, perms, lavanderia_id):
        payload["role_ref"] = role_ref
        payload["perms"] = perms

    monkeypatch.setattr(
        "backend.api.routers.roles.set_permissions_for_role",
        fake_set,
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.count_settings_admins",
        lambda lavanderia_id, **kw: 1,
    )
    response = _client(monkeypatch, current_user_role="admin").put(
        "/roles/2/permissions",
        headers=_auth_headers("settings"),
        json={"permissions": ["register_sale", "movements"]},
    )
    assert response.status_code == 200
    assert payload == {"role_ref": 2, "perms": ["register_sale", "movements"]}


# ---------- guard: último admin ----------


def test_toggle_role_blocks_when_last_admin(monkeypatch):
    """Desactivar el rol que tiene al único admin del tenant debe fallar."""
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {
            "id": role_id,
            "name": "supervisor",
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.count_settings_admins",
        lambda lavanderia_id, **kw: 0,
    )
    response = _client(monkeypatch, current_user_role="admin").patch(
        "/roles/3/status",
        headers=_auth_headers("settings"),
    )
    assert response.status_code == 400
    assert "administradores" in response.json()["detail"]


def test_replace_perms_blocks_when_last_admin(monkeypatch):
    """Quitarle settings al rol del único admin debe fallar."""
    monkeypatch.setattr(
        "backend.api.routers.roles.get_role_by_id",
        lambda role_id, lavanderia_id: {
            "id": role_id,
            "name": "supervisor",
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.set_permissions_for_role",
        lambda role_ref, perms, lavanderia_id: None,
    )
    monkeypatch.setattr(
        "backend.api.routers.roles.count_settings_admins",
        lambda lavanderia_id, **kw: 0,
    )
    response = _client(monkeypatch, current_user_role="admin").put(
        "/roles/3/permissions",
        headers=_auth_headers("settings"),
        json={"permissions": ["register_sale"]},
    )
    assert response.status_code == 400
    assert "administradores" in response.json()["detail"]
