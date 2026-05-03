"""Sistema central de notificaciones toast para la UI."""

import streamlit as st

_KEY = "_pending_toasts"


def notify(message: str, icon: str = "✅"):
    """Encola un mensaje toast para mostrarse en el proximo render."""
    st.session_state.setdefault(_KEY, []).append({"message": message, "icon": icon})


def notify_error(message: str):
    """Encola un mensaje de error toast."""
    notify(message, icon="❌")


def show_notifications():
    """Muestra todos los toasts pendientes. Llamar una vez por render en app.py."""
    for toast in st.session_state.pop(_KEY, []):
        st.toast(toast["message"], icon=toast["icon"])
