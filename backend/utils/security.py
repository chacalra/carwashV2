"""Utilidades de seguridad: hashing, verificacion y tokens firmados."""

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone


DEFAULT_TOKEN_EXPIRES_MINUTES = 60


class TokenError(ValueError):
    """Error de validacion para tokens de acceso."""


def _b64url_encode(raw: bytes) -> str:
    """Codifica bytes en Base64 URL-safe sin padding."""
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64url_decode(value: str) -> bytes:
    """Decodifica Base64 URL-safe restaurando el padding necesario."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _token_secret() -> bytes:
    """Obtiene la clave de firma para tokens."""
    return os.environ.get("AUTH_TOKEN_SECRET", "dev-secret-change-me").encode()


def _token_expiration_minutes() -> int:
    """Obtiene la duracion configurada para el token."""
    raw_value = os.environ.get("AUTH_TOKEN_EXPIRES_MINUTES")
    if raw_value is None:
        return DEFAULT_TOKEN_EXPIRES_MINUTES

    try:
        minutes = int(raw_value)
    except ValueError as exc:
        raise ValueError("AUTH_TOKEN_EXPIRES_MINUTES debe ser un entero.") from exc

    if minutes <= 0:
        raise ValueError("AUTH_TOKEN_EXPIRES_MINUTES debe ser mayor que cero.")
    return minutes


def create_access_token(*, user_id: int, lavanderia_id: int, permissions: list[str]):
    """Crea un token HS256 con expiracion y datos minimos del usuario."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=_token_expiration_minutes())

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "lavanderia_id": lavanderia_id,
        "permissions": list(dict.fromkeys(permissions)),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    header_segment = _b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode()
    )
    payload_segment = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    signing_input = f"{header_segment}.{payload_segment}".encode()
    signature = hmac.new(_token_secret(), signing_input, hashlib.sha256).digest()
    token = f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"
    return token, expires_at


def decode_access_token(token: str) -> dict:
    """Valida y decodifica un token HS256."""
    if not token or not token.strip():
        raise TokenError("Token faltante.")

    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise TokenError("Token invalido.") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode()
    expected_signature = hmac.new(_token_secret(), signing_input, hashlib.sha256).digest()

    try:
        actual_signature = _b64url_decode(signature_segment)
    except Exception as exc:
        raise TokenError("Token invalido.") from exc

    if not hmac.compare_digest(actual_signature, expected_signature):
        raise TokenError("Token invalido.")

    try:
        header = json.loads(_b64url_decode(header_segment))
        payload = json.loads(_b64url_decode(payload_segment))
    except Exception as exc:
        raise TokenError("Token invalido.") from exc

    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise TokenError("Token invalido.")

    exp = payload.get("exp")
    user_id = payload.get("user_id")
    lavanderia_id = payload.get("lavanderia_id")
    permissions = payload.get("permissions")

    if not isinstance(exp, int) or not isinstance(user_id, int) or not isinstance(
        lavanderia_id, int
    ):
        raise TokenError("Token invalido.")
    if not isinstance(permissions, list) or any(not isinstance(item, str) for item in permissions):
        raise TokenError("Token invalido.")

    if exp <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenError("Token expirado.")

    return payload


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
