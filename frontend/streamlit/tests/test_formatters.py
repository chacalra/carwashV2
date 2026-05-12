"""Tests para utils/formatters.py."""

import pytest

from frontend.streamlit.utils.formatters import is_company_name, normalize_razon_social


# --- normalize_razon_social ---

def test_normalize_palabras_comunes():
    assert normalize_razon_social("ramon chacal") == "Ramon Chacal"


def test_normalize_sigla_srl():
    assert normalize_razon_social("panaderia la negrita s.r.l.") == "Panaderia La Negrita S.R.L."


def test_normalize_sigla_sa():
    assert normalize_razon_social("interpan s.a.") == "Interpan S.A."


def test_normalize_sigla_saeca():
    assert normalize_razon_social("empresa s.a.e.c.a.") == "Empresa S.A.E.C.A."


def test_normalize_mayusculas_mezcladas():
    assert normalize_razon_social("PANADERIA La Negrita S.R.L.") == "Panaderia La Negrita S.R.L."


def test_normalize_espacios_extremos():
    assert normalize_razon_social("  distribuidora don juan s.r.l.  ") == "Distribuidora Don Juan S.R.L."


def test_normalize_none_devuelve_none():
    assert normalize_razon_social(None) is None


def test_normalize_vacio_devuelve_vacio():
    assert normalize_razon_social("") == ""


# --- is_company_name ---

def test_empresa_con_srl():
    assert is_company_name("Panaderia La Negrita S.R.L.") is True


def test_empresa_con_sa():
    assert is_company_name("INTERPAN S.A.") is True


def test_empresa_con_saeca():
    assert is_company_name("Empresa S.A.E.C.A.") is True


def test_persona_fisica_no_es_empresa():
    assert is_company_name("Ramon Chacal") is False


def test_apellido_compuesto_no_es_empresa():
    assert is_company_name("Natalia Saldivar") is False


def test_none_no_es_empresa():
    assert is_company_name(None) is False


def test_sigla_sin_puntos_no_es_empresa():
    # "SA" sin puntos no se reconoce como sigla empresarial
    assert is_company_name("Empresa SA") is False


def test_sigla_con_puntos_al_inicio():
    assert is_company_name("S.R.L. Nombre Raro") is True
