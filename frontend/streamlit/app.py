"""Punto de entrada principal de la app Streamlit."""

from pathlib import Path

from PIL import Image
import streamlit as st

from backend.database.schema import create_tables
from backend.database.seed import seed_initial_data
from backend.services.auth_service import get_allowed_views
from frontend.streamlit.ui.dashboard import render_dashboard
from frontend.streamlit.ui.export_view import render_export_view
from frontend.streamlit.ui.expenses_form import render_expense_form
from frontend.streamlit.ui.login_view import render_login
from frontend.streamlit.ui.movements_view import render_movements_view
from frontend.streamlit.ui.sales_edit_view import render_sales_edit_view
from frontend.streamlit.ui.sales_form import render_sales_form
from frontend.streamlit.ui.sales_management_view import render_sales_management_view
from frontend.streamlit.ui.settings_view import render_settings_view
from frontend.streamlit.utils.notifications import show_notifications


@st.cache_resource
def initialize_app():
    """Inicializa la base de datos y los datos base del sistema (una sola vez por instancia)."""
    create_tables()
    seed_initial_data()


def render_sidebar():
    """Renderiza el sidebar con info del usuario, navegacion y boton de logout."""
    st.sidebar.image("frontend/streamlit/images/sin-fondo.png", width='stretch')
    st.sidebar.caption(f"Usuario: **{st.session_state['user_name']}** ({st.session_state['user_role']})")

    if st.sidebar.button("Cerrar sesion", width='stretch'):
        for key in [
            "logged_in",
            "user_id",
            "user_name",
            "user_role",
            "permissions",
            "lavanderia_id",
            "lavanderia_name",
        ]:
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
    elif current_view == "Registrar venta":
        render_sales_form()
    elif current_view == "Editar venta":
        render_sales_edit_view()
    elif current_view == "Gestionar ventas":
        render_sales_management_view()
    elif current_view == "Registrar egreso":
        render_expense_form()
    elif current_view == "Movimientos":
        render_movements_view()
    elif current_view == "Exportar":
        render_export_view()
    elif current_view == "Configuracion":
        render_settings_view()


if __name__ == "__main__":
    main()
