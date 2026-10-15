"""Tests para utils/security.py."""

import pytest
from backend.utils.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_formato():
    h = hash_password("test123")
    esquema, iteraciones, salt, derivado = h.split("$")
    assert esquema == "pbkdf2_sha256"
    assert int(iteraciones) >= 600_000
    assert len(salt) == 32  # 16 bytes en hex
    assert len(derivado) == 64  # SHA-256 en hex


def test_hash_password_unico():
    """Dos hashes de la misma contrasena deben ser distintos (salts distintos)."""
    h1 = hash_password("misma_contrasena")
    h2 = hash_password("misma_contrasena")
    assert h1 != h2


def test_verify_contrasena_correcta():
    h = hash_password("mi_pass")
    assert verify_password("mi_pass", h) is True


def test_verify_contrasena_incorrecta():
    h = hash_password("correcta")
    assert verify_password("incorrecta", h) is False


def test_verify_hash_invalido():
    assert verify_password("cualquiera", "hash_sin_dos_puntos") is False


def test_verify_hash_vacio():
    assert verify_password("cualquiera", "") is False


def test_verify_hash_legacy_compatible():
    import hashlib

    salt = "a" * 64
    legacy = f"{salt}:{hashlib.sha256((salt + 'legacy-pass').encode()).hexdigest()}"
    assert verify_password("legacy-pass", legacy) is True
    assert verify_password("wrong-pass", legacy) is False


def test_create_and_decode_access_token():
    token, expires_at = create_access_token(
        user_id=4,
        lavanderia_id=9,
        permissions=["dashboard", "register_sale"],
    )

    payload = decode_access_token(token)

    assert payload["user_id"] == 4
    assert payload["lavanderia_id"] == 9
    assert payload["permissions"] == ["dashboard", "register_sale"]
    assert payload["exp"] == int(expires_at.timestamp())


def test_decode_access_token_rejects_tampered_signature():
    token, _ = create_access_token(
        user_id=1,
        lavanderia_id=2,
        permissions=["dashboard"],
    )
    header, payload, signature = token.split(".")
    tampered_signature = ("a" if signature[0] != "a" else "b") + signature[1:]
    tampered = f"{header}.{payload}.{tampered_signature}"

    with pytest.raises(TokenError, match="Token invalido"):
        decode_access_token(tampered)
