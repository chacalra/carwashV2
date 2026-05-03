"""Helpers para resolver el tenant actual desde Streamlit o argumentos explicitos."""


def get_current_lavanderia_id():
    """Devuelve la lavanderia actual desde session_state si existe."""
    try:
        import streamlit as st
    except Exception:
        return None

    return st.session_state.get("lavanderia_id")


def resolve_lavanderia_id(lavanderia_id=None, *, required=False):
    """Resuelve el tenant actual priorizando el valor explicito."""
    resolved = lavanderia_id if lavanderia_id is not None else get_current_lavanderia_id()

    if required and resolved is None:
        raise ValueError("Hace falta una lavanderia activa para ejecutar esta operacion.")

    return resolved
