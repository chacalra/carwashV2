"""HTTP error helpers for routers."""

from typing import NoReturn

from fastapi import HTTPException, status

_NOT_FOUND_KEYWORDS = ("no existe",)
_CONFLICT_KEYWORDS = ("ya fue anulado", "ya fue anulada", "ya existe")


def raise_service_error(exc: ValueError) -> NoReturn:
    """Routes a service ValueError to the appropriate HTTP error.

    - "no existe" in message → 404 Not Found
    - "ya fue anulado/a" or "ya existe" in message → 409 Conflict
    - anything else → 400 Bad Request
    """
    message = str(exc)
    if any(kw in message for kw in _NOT_FOUND_KEYWORDS):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
    if any(kw in message for kw in _CONFLICT_KEYWORDS):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
