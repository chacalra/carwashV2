"""Vista de configuracion: CRUD de catalogos administrables."""

import pandas as pd
import streamlit as st

from repositories.expense_categories_repository import get_all_categories
from repositories.products_repository import get_all_products
from repositories.role_permissions_repository import get_permissions_for_role
from repositories.roles_repository import get_all_roles
from repositories.services_repository import get_all_services
from repositories.users_repository import get_all_users
from repositories.vehicle_types_repository import get_all_vehicle_types
from services.auth_service import PERMISSIONS
from services.catalog_service import (
    add_category,
    add_product,
    add_role,
    add_service,
    add_user,
    add_vehicle_type,
    change_user_password,
    edit_user,
    remove_category,
    remove_product,
    remove_service,
    remove_vehicle_type,
    rename_category,
    rename_product,
    rename_service,
    rename_vehicle_type,
    save_role_permissions,
    toggle_category_status,
    toggle_product_status,
    toggle_role_status,
    toggle_service_status,
    toggle_user_status,
    toggle_vehicle_type_status,
)
from utils.notifications import notify


def _render_toggle(selected, toggle_fn, confirm_key):
    """Renderiza boton de activar/desactivar con confirmacion de dos pasos."""
    if selected["is_active"]:
        if st.session_state.get(confirm_key):
            st.warning(f"¿Confirmar desactivacion de **'{selected['name']}'**?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Si, desactivar", key=f"yes_{confirm_key}", type="primary"):
                    toggle_fn(selected["id"])
                    st.session_state.pop(confirm_key, None)
                    notify(f"'{selected['name']}' desactivado.")
                    st.rerun()
            with col_no:
                if st.button("Cancelar", key=f"no_{confirm_key}"):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
        else:
            if st.button("Desactivar", key=f"deact_{confirm_key}"):
                st.session_state[confirm_key] = True
                st.rerun()
    else:
        if st.button("Activar", key=f"act_{confirm_key}"):
            toggle_fn(selected["id"])
            notify(f"'{selected['name']}' activado.")
            st.rerun()


def _catalog_tab(
    items,
    item_label,
    add_fn,
    rename_fn,
    toggle_fn,
    add_form_key,
    edit_form_key,
    select_key,
    delete_fn=None,
):
    """Renderiza un tab generico de catalogo (listado + agregar + editar/togglear)."""
    if items:
        df = pd.DataFrame([dict(i) for i in items])
        df["Estado"] = df["is_active"].map({1: "Activo", 0: "Inactivo"})
        st.dataframe(
            df[["name", "Estado"]].rename(columns={"name": "Nombre"}),
            width='stretch',
            hide_index=True,
        )
    else:
        st.info(f"No hay {item_label.lower()}s registrados.")

    st.divider()

    with st.expander(f"Agregar {item_label.lower()}"):
        with st.form(add_form_key, clear_on_submit=True):
            new_name = st.text_input("Nombre")
            if st.form_submit_button("Agregar"):
                try:
                    add_fn(new_name)
                    notify(f"{item_label} '{new_name}' agregado correctamente.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    if items:
        st.subheader("Editar / Activar-Desactivar")
        options = {
            f"{i['name']} ({'Activo' if i['is_active'] else 'Inactivo'})": i["id"]
            for i in items
        }
        selected_label = st.selectbox(
            f"Seleccionar {item_label.lower()}",
            list(options.keys()),
            key=select_key,
        )
        selected_id = options[selected_label]
        selected = next(i for i in items if i["id"] == selected_id)

        with st.form(f"{edit_form_key}_{selected_id}"):
            edited_name = st.text_input("Nombre", value=selected["name"])
            save = st.form_submit_button("Guardar nombre")

        if save:
            try:
                rename_fn(selected_id, edited_name)
                notify("Nombre actualizado correctamente.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        _render_toggle(selected, toggle_fn, confirm_key=f"confirm_{select_key}")

        if delete_fn:
            st.divider()
            delete_confirm_key = f"confirm_delete_{select_key}"
            if st.session_state.get(delete_confirm_key):
                st.error(f"¿Eliminar permanentemente **'{selected['name']}'**? Esta accion no se puede deshacer.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Si, eliminar", key=f"yes_{delete_confirm_key}", type="primary"):
                        try:
                            delete_fn(selected["id"])
                            st.session_state.pop(delete_confirm_key, None)
                            notify(f"'{selected['name']}' eliminado.")
                            st.rerun()
                        except ValueError as error:
                            st.session_state.pop(delete_confirm_key, None)
                            st.error(str(error))
                with col_no:
                    if st.button("Cancelar", key=f"no_{delete_confirm_key}"):
                        st.session_state.pop(delete_confirm_key, None)
                        st.rerun()
            else:
                if st.button("Eliminar", key=f"del_{select_key}"):
                    st.session_state[delete_confirm_key] = True
                    st.rerun()


def render_services_tab():
    _catalog_tab(
        items=get_all_services(),
        item_label="Servicio",
        add_fn=add_service,
        rename_fn=rename_service,
        toggle_fn=toggle_service_status,
        delete_fn=remove_service,
        add_form_key="add_service_form",
        edit_form_key="edit_service_form",
        select_key="select_service",
    )


def render_products_tab():
    _catalog_tab(
        items=get_all_products(),
        item_label="Producto",
        add_fn=add_product,
        rename_fn=rename_product,
        toggle_fn=toggle_product_status,
        delete_fn=remove_product,
        add_form_key="add_product_form",
        edit_form_key="edit_product_form",
        select_key="select_product",
    )


def render_categories_tab():
    _catalog_tab(
        items=get_all_categories(),
        item_label="Categoria",
        add_fn=add_category,
        rename_fn=rename_category,
        toggle_fn=toggle_category_status,
        delete_fn=remove_category,
        add_form_key="add_category_form",
        edit_form_key="edit_category_form",
        select_key="select_category",
    )


def render_vehicle_types_tab():
    _catalog_tab(
        items=get_all_vehicle_types(),
        item_label="Tipo de vehiculo",
        add_fn=add_vehicle_type,
        rename_fn=rename_vehicle_type,
        toggle_fn=toggle_vehicle_type_status,
        delete_fn=remove_vehicle_type,
        add_form_key="add_vehicle_type_form",
        edit_form_key="edit_vehicle_type_form",
        select_key="select_vehicle_type",
    )


def render_roles_tab():
    """Tab de gestion de roles y sus permisos."""
    roles = get_all_roles()

    if roles:
        df = pd.DataFrame([dict(r) for r in roles])
        df["Estado"] = df["is_active"].map({1: "Activo", 0: "Inactivo"})
        st.dataframe(
            df[["name", "Estado"]].rename(columns={"name": "Rol"}),
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No hay roles registrados.")

    st.divider()

    with st.expander("Agregar rol"):
        with st.form("add_role_form", clear_on_submit=True):
            new_role_name = st.text_input("Nombre del rol")
            if st.form_submit_button("Agregar rol"):
                try:
                    add_role(new_role_name)
                    notify(f"Rol '{new_role_name}' creado. Asignale permisos abajo.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    if roles:
        st.subheader("Permisos por rol")
        role_options = {r["name"]: r for r in roles}
        selected_role_name = st.selectbox(
            "Seleccionar rol",
            list(role_options.keys()),
            key="select_role_perms",
        )
        selected_role = role_options[selected_role_name]

        current_perms = get_permissions_for_role(selected_role_name)

        with st.form(f"role_permissions_form_{selected_role_name}"):
            st.write(f"Permisos para **{selected_role_name}**:")
            selected_perms = []
            for perm_key, perm_label in PERMISSIONS.items():
                checked = st.checkbox(perm_label, value=perm_key in current_perms, key=f"perm_{selected_role_name}_{perm_key}")
                if checked:
                    selected_perms.append(perm_key)
            save_perms = st.form_submit_button("Guardar permisos")

        if save_perms:
            save_role_permissions(selected_role_name, selected_perms)
            notify(f"Permisos de '{selected_role_name}' actualizados.")
            st.rerun()

        _render_toggle(
            {"id": selected_role["id"], "name": selected_role_name, "is_active": selected_role["is_active"]},
            toggle_fn=toggle_role_status,
            confirm_key="confirm_role",
        )


def render_users_tab():
    """Tab de gestion de usuarios."""
    users = get_all_users()
    roles = get_all_roles()
    role_names = [r["name"] for r in roles] if roles else []

    if users:
        df = pd.DataFrame([dict(u) for u in users])
        df["Estado"] = df["is_active"].map({1: "Activo", 0: "Inactivo"})
        st.dataframe(
            df[["name", "role", "Estado"]].rename(
                columns={"name": "Nombre", "role": "Rol"}
            ),
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No hay usuarios registrados.")

    st.divider()

    with st.expander("Agregar usuario"):
        with st.form("add_user_form", clear_on_submit=True):
            new_name = st.text_input("Nombre")
            new_role = st.selectbox("Rol", options=role_names if role_names else ["(sin roles)"])
            new_password = st.text_input("Contrasena inicial", type="password")
            if st.form_submit_button("Agregar usuario"):
                try:
                    add_user(new_name, new_role, new_password)
                    notify(f"Usuario '{new_name}' creado correctamente.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    if users:
        st.subheader("Editar / Activar-Desactivar")
        user_options = {
            f"{u['name']} ({u['role']}, {'Activo' if u['is_active'] else 'Inactivo'})": u["id"]
            for u in users
        }
        selected_label = st.selectbox("Seleccionar usuario", list(user_options.keys()), key="select_user")
        selected_id = user_options[selected_label]
        selected = next(u for u in users if u["id"] == selected_id)

        with st.form(f"edit_user_form_{selected_id}"):
            edited_name = st.text_input("Nombre", value=selected["name"])
            role_index = role_names.index(selected["role"]) if selected["role"] in role_names else 0
            edited_role = st.selectbox("Rol", options=role_names if role_names else [selected["role"]], index=role_index)
            save = st.form_submit_button("Guardar cambios")

        if save:
            try:
                edit_user(selected_id, edited_name, edited_role)
                notify("Usuario actualizado correctamente.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        _render_toggle(
            {"id": selected["id"], "name": selected["name"], "is_active": selected["is_active"]},
            toggle_fn=toggle_user_status,
            confirm_key="confirm_user",
        )

        st.subheader("Cambiar contrasena")
        with st.form("change_password_form", clear_on_submit=True):
            new_pw = st.text_input(f"Nueva contrasena para {selected['name']}", type="password")
            if st.form_submit_button("Cambiar contrasena"):
                try:
                    change_user_password(selected_id, new_pw)
                    notify("Contrasena actualizada correctamente.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))


def render_settings_view():
    """Renderiza la pantalla de configuracion de catalogos."""
    st.title("Configuracion")
    st.write("Administra los catalogos del sistema.")

    tabs = st.tabs([
        "Servicios",
        "Productos",
        "Categorias de egreso",
        "Tipos de vehiculo",
        "Roles y Permisos",
        "Usuarios",
    ])

    with tabs[0]:
        render_services_tab()
    with tabs[1]:
        render_products_tab()
    with tabs[2]:
        render_categories_tab()
    with tabs[3]:
        render_vehicle_types_tab()
    with tabs[4]:
        render_roles_tab()
    with tabs[5]:
        render_users_tab()
