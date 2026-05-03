"""Utilidades de seguridad: hashing y verificacion de contrasenas."""

import hashlib
import os


def hash_password(password: str) -> str:
    """Genera un hash seguro para una contrasena usando SHA-256 con salt aleatorio."""
    salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica una contrasena contra su hash almacenado."""
    try:
        salt, hashed = stored_hash.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except Exception:
        return False
