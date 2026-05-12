"""Tests para backend/cli/branding.py — validaciones puras y update parcial."""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.cli.branding import (
    clear_branding,
    normalize_hex,
    normalize_url,
    set_branding,
    show_branding,
)


# --- normalize_hex ---

def test_normalize_hex_acepta_con_y_sin_hash():
    assert normalize_hex("#FF0000") == "#FF0000"
    assert normalize_hex("FF0000") == "#FF0000"


def test_normalize_hex_normaliza_a_mayusculas():
    assert normalize_hex("#ff00aa") == "#FF00AA"
    assert normalize_hex("00ff00") == "#00FF00"


def test_normalize_hex_acepta_3_y_8_chars():
    assert normalize_hex("#fff") == "#FFF"
    assert normalize_hex("FF000080") == "#FF000080"


def test_normalize_hex_rechaza_basura():
    with pytest.raises(ValueError, match="hex inválido"):
        normalize_hex("rojo")
    with pytest.raises(ValueError):
        normalize_hex("#GG0000")
    with pytest.raises(ValueError):
        normalize_hex("#1234")  # 4 chars no es válido


def test_normalize_hex_none_y_vacio_devuelven_none():
    assert normalize_hex(None) is None
    assert normalize_hex("") is None
    assert normalize_hex("   ") is None


# --- normalize_url ---

def test_normalize_url_acepta_http_y_https():
    assert normalize_url("https://cdn.example/a.png") == "https://cdn.example/a.png"
    assert normalize_url("http://localhost:8080/x.png") == "http://localhost:8080/x.png"


def test_normalize_url_rechaza_relativas():
    with pytest.raises(ValueError, match="inválida"):
        normalize_url("/uploads/x.png")
    with pytest.raises(ValueError):
        normalize_url("ftp://x/y")


def test_normalize_url_none_y_vacio_devuelven_none():
    assert normalize_url(None) is None
    assert normalize_url("") is None


# --- set_branding (con mocks de DB) ---

def _fake_lavanderia():
    return SimpleNamespace(
        logo_url=None,
        logo_url_dark=None,
        color_primario=None,
        color_secundario=None,
        mostrar_marca_mukusoft=True,
    )


def _patch_repo(monkeypatch, lavanderia):
    monkeypatch.setattr(
        "backend.cli.branding.get_lavanderia_by_subdominio",
        lambda session, subdomain: lavanderia,
    )


def test_set_branding_actualiza_solo_lo_pasado(monkeypatch):
    lav = _fake_lavanderia()
    lav.color_primario = "#OLD"  # representa estado anterior
    _patch_repo(monkeypatch, lav)

    session = MagicMock()
    result = set_branding(
        session,
        subdomain="demo",
        logo="https://cdn.example/a.png",
        primary="ff0000",
    )

    assert lav.logo_url == "https://cdn.example/a.png"
    assert lav.color_primario == "#FF0000"
    # No se pasó secondary → no se toca
    assert lav.color_secundario is None
    # Y mostrar_marca_mukusoft tampoco
    assert lav.mostrar_marca_mukusoft is True

    assert result["color_primario"] == "#FF0000"
    session.commit.assert_called_once()


def test_set_branding_normaliza_hex(monkeypatch):
    lav = _fake_lavanderia()
    _patch_repo(monkeypatch, lav)

    set_branding(MagicMock(), subdomain="demo", primary="ff0000", secondary="#00ff00")

    assert lav.color_primario == "#FF0000"
    assert lav.color_secundario == "#00FF00"


def test_set_branding_string_vacio_borra_campo(monkeypatch):
    lav = _fake_lavanderia()
    lav.logo_url = "https://old.example/x.png"
    _patch_repo(monkeypatch, lav)

    set_branding(MagicMock(), subdomain="demo", logo="")

    assert lav.logo_url is None


def test_set_branding_show_mukusoft_toggle(monkeypatch):
    lav = _fake_lavanderia()
    _patch_repo(monkeypatch, lav)

    set_branding(MagicMock(), subdomain="demo", show_mukusoft=False)
    assert lav.mostrar_marca_mukusoft is False

    set_branding(MagicMock(), subdomain="demo", show_mukusoft=True)
    assert lav.mostrar_marca_mukusoft is True


def test_set_branding_falla_si_subdomain_no_existe(monkeypatch):
    monkeypatch.setattr(
        "backend.cli.branding.get_lavanderia_by_subdominio",
        lambda session, subdomain: None,
    )
    with pytest.raises(ValueError, match="No existe ningún tenant"):
        set_branding(MagicMock(), subdomain="ghost", primary="#FF0000")


def test_set_branding_propaga_error_de_validacion(monkeypatch):
    lav = _fake_lavanderia()
    _patch_repo(monkeypatch, lav)

    with pytest.raises(ValueError, match="hex inválido"):
        set_branding(MagicMock(), subdomain="demo", primary="rojo")


# --- clear_branding ---

def test_clear_branding_resetea_visuales_no_toca_mukusoft(monkeypatch):
    lav = _fake_lavanderia()
    lav.logo_url = "https://x.com/a.png"
    lav.logo_url_dark = "https://x.com/a-dark.png"
    lav.color_primario = "#FF0000"
    lav.color_secundario = "#00FF00"
    lav.mostrar_marca_mukusoft = False  # decisión previa, no se toca
    _patch_repo(monkeypatch, lav)

    clear_branding(MagicMock(), subdomain="demo")

    assert lav.logo_url is None
    assert lav.logo_url_dark is None
    assert lav.color_primario is None
    assert lav.color_secundario is None
    # Sigue como estaba
    assert lav.mostrar_marca_mukusoft is False


# --- show_branding ---

def test_show_branding_devuelve_estado_actual(monkeypatch):
    lav = _fake_lavanderia()
    lav.logo_url = "https://x.com/a.png"
    lav.color_primario = "#FF0000"
    _patch_repo(monkeypatch, lav)

    result = show_branding(MagicMock(), subdomain="demo")

    assert result == {
        "logo_url": "https://x.com/a.png",
        "logo_url_dark": None,
        "color_primario": "#FF0000",
        "color_secundario": None,
        "mostrar_marca_mukusoft": True,
    }
