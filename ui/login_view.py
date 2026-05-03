"""Vista de inicio de sesion."""

import streamlit as st

from services.auth_service import login


def render_login():
    """Renderiza la pantalla de login. Setea session_state al autenticar."""
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.image("images/sin-fondo.png", width='stretch')
        st.subheader("Iniciar sesion")

        with st.form("login_form"):
            name = st.text_input("Usuario")
            password = st.text_input("Contrasena", type="password")
            submitted = st.form_submit_button("Ingresar", width='stretch')

        if submitted:
            try:
                user, permissions = login(name, password)
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["user_name"] = user["name"]
                st.session_state["user_role"] = user["role"]
                st.session_state["permissions"] = permissions
                st.rerun()
            except ValueError as error:
                st.error(str(error))

