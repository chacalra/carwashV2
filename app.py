"""Punto de entrada principal de la app Streamlit."""

from pathlib import Path

from PIL import Image
import streamlit as st

from database.schema import create_tables
from database.seed import seed_initial_data
from services.auth_service import get_allowed_views
from ui.dashboard import render_dashboard
from ui.edit_income_view import render_edit_income_view
from ui.void_incomes_view import render_void_incomes_view
from ui.export_view import render_export_view
from ui.expenses_form import render_expense_form
from ui.incomes_form import render_income_form
from ui.login_view import render_login
from ui.movements_view import render_movements_view
from ui.settings_view import render_settings_view
from utils.notifications import show_notifications


@st.cache_resource
def initialize_app():
    """Inicializa la base de datos y los datos base del sistema (una sola vez por instancia)."""
    create_tables()
    seed_initial_data()


def render_sidebar():
    """Renderiza el sidebar con info del usuario, navegacion y boton de logout."""
    st.sidebar.image("images/sin-fondo.png", width='stretch')
    st.sidebar.caption(f"Usuario: **{st.session_state['user_name']}** ({st.session_state['user_role']})")

    if st.sidebar.button("Cerrar sesion", width='stretch'):
        for key in ["logged_in", "user_id", "user_name", "user_role", "permissions"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.sidebar.divider()

    allowed = get_allowed_views(st.session_state.get("permissions", []))
    if not allowed:
        st.sidebar.warning("Sin permisos asignados.")
        return None

    return st.sidebar.radio("Ir a", allowed)


@st.cache_resource
def _load_logo():
    return Image.open(Path(__file__).parent / "images" / "sin-fondo.png")


def main():
    """Orquesta la inicializacion y el render principal."""
    st.set_page_config(
        page_title="AutoCare",
        page_icon=_load_logo(),
        layout="wide",
    )

    initialize_app()

    if not st.session_state.get("logged_in"):
        render_login()
        st.stop()

    show_notifications()
    current_view = render_sidebar()

    if current_view == "Dashboard":
        render_dashboard()
    elif current_view == "Registrar ingreso":
        render_income_form()
    elif current_view == "Editar ingreso":
        render_edit_income_view()
    elif current_view == "Registrar egreso":
        render_expense_form()
    elif current_view == "Movimientos":
        render_movements_view()
    elif current_view == "Gestionar ingresos":
        render_void_incomes_view()
    elif current_view == "Exportar":
        render_export_view()
    elif current_view == "Configuracion":
        render_settings_view()


if __name__ == "__main__":
    main()
