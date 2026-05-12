"""Lógica del comando set/clear/show branding.

Vive separada del entrypoint para que sea testeable: las funciones reciben
`session` y devuelven dicts. Ningún `print`, ninguna lectura de argv.
El __main__.py se ocupa del wiring con argparse.
"""

import re
from urllib.parse import urlparse

from backend.repositories.lavanderias_repository import (
    get_lavanderia_branding,
    get_lavanderia_by_subdominio,
    update_lavanderia_branding,
)


HEX_COLOR_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def normalize_hex(value):
    """Valida y normaliza un color hex.

    Acepta `#RGB`, `#RRGGBB`, `#RRGGBBAA` (con o sin `#`).
    Devuelve siempre con `#` y en mayúsculas. Lanza ValueError si no parsea.
    """
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    match = HEX_COLOR_RE.match(raw)
    if match is None:
        raise ValueError(f"Color hex inválido: {value!r}. Usá #RGB, #RRGGBB o #RRGGBBAA.")
    return f"#{match.group(1).upper()}"


def normalize_url(value):
    """Valida una URL http/https. Devuelve la URL tal cual o lanza ValueError."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL inválida: {value!r}. Debe empezar con http:// o https://.")
    return raw


def find_tenant_or_raise(session, subdomain):
    """Busca por subdominio o lanza ValueError con mensaje claro."""
    lavanderia = get_lavanderia_by_subdominio(session, subdomain)
    if lavanderia is None:
        raise ValueError(f"No existe ningún tenant con subdominio {subdomain!r}.")
    return lavanderia


def set_branding(
    session,
    *,
    subdomain,
    logo=None,
    logo_dark=None,
    primary=None,
    secondary=None,
    show_mukusoft=None,
):
    """Aplica branding parcial al tenant. Solo modifica los campos pasados.

    `None` significa "no tocar" (sentinel del repo). Si querés borrar un campo,
    pasalo como cadena vacía y se normaliza a None.
    """
    lavanderia = find_tenant_or_raise(session, subdomain)

    kwargs = {}
    if logo is not None:
        kwargs["logo_url"] = normalize_url(logo) if logo != "" else None
    if logo_dark is not None:
        kwargs["logo_url_dark"] = normalize_url(logo_dark) if logo_dark != "" else None
    if primary is not None:
        kwargs["color_primario"] = normalize_hex(primary) if primary != "" else None
    if secondary is not None:
        kwargs["color_secundario"] = normalize_hex(secondary) if secondary != "" else None
    if show_mukusoft is not None:
        kwargs["mostrar_marca_mukusoft"] = bool(show_mukusoft)

    update_lavanderia_branding(session, lavanderia, **kwargs)
    session.commit()
    return get_lavanderia_branding(lavanderia)


def clear_branding(session, *, subdomain):
    """Resetea los 4 campos visuales (logo, logo_dark, primary, secondary).

    Mantiene `mostrar_marca_mukusoft` como esté: la decisión de mostrar/ocultar
    Mukusoft es ortogonal al branding visual del cliente.
    """
    lavanderia = find_tenant_or_raise(session, subdomain)
    update_lavanderia_branding(
        session,
        lavanderia,
        logo_url=None,
        logo_url_dark=None,
        color_primario=None,
        color_secundario=None,
    )
    session.commit()
    return get_lavanderia_branding(lavanderia)


def show_branding(session, *, subdomain):
    """Devuelve el estado actual de branding del tenant."""
    lavanderia = find_tenant_or_raise(session, subdomain)
    return get_lavanderia_branding(lavanderia)
