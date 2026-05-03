"""Tests para utils/security.py."""

import pytest
from utils.security import hash_password, verify_password


def test_hash_password_formato():
    h = hash_password("test123")
    partes = h.split(":")
    assert len(partes) == 2
    assert len(partes[0]) == 64  # salt: 32 bytes en hex
    assert len(partes[1]) == 64  # sha256 en hex


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
