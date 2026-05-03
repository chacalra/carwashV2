"""Helpers de formato para mostrar numeros de manera legible."""

import re


def is_company_name(name):
    """Detecta si una razon social corresponde a una empresa (tiene sigla tipo S.A., S.R.L., etc.)."""
    if not isinstance(name, str):
        return False
    return bool(re.search(r'\b[A-Z](\.[A-Z])+\.?(\s|$)', name))


def normalize_razon_social(value):
    """Normaliza razon social: title case para palabras, uppercase para siglas (s.r.l. -> S.R.L.)."""
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return value

    def _normalize_word(word):
        # Sigla: letras de un caracter separadas por puntos, ej: s.r.l. s.a. s.a.e.c.a.
        if re.match(r'^[a-zA-Z](\.[a-zA-Z])+\.?$', word):
            return word.upper()
        return word.capitalize()

    return ' '.join(_normalize_word(w) for w in value.split())


def format_number(value, decimals=0):
    """Formatea numeros con separador de miles usando punto."""
    if value is None:
        return "-"

    formatted_value = f"{value:,.{decimals}f}"
    return formatted_value.replace(",", "_").replace(".", ",").replace("_", ".")


def format_currency(value):
    """Formatea un monto como guaranies."""
    return f"Gs. {format_number(value)}"


def parse_amount_input(value):
    """Convierte un monto escrito como texto a float.

    Acepta formatos como:
    - 50000
    - 50.000
    - 50,000
    """
    if value is None:
        raise ValueError("El monto es obligatorio.")

    normalized_value = str(value).strip()
    if not normalized_value:
        raise ValueError("El monto es obligatorio.")

    normalized_value = normalized_value.replace(".", "").replace(",", "")

    if not normalized_value.isdigit():
        raise ValueError(
            "El monto debe contener solo numeros, puntos o comas como separadores."
        )

    return float(normalized_value)
