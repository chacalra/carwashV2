"""Tests de integracion para los repositorios (usan base de datos temporal)."""

import pytest
import sqlite3

import pickle

from repositories.services_repository import (
    create_service,
    get_all_services,
    get_active_services,
    get_service_by_id,
    update_service_name,
    toggle_service,
)
from repositories.expense_categories_repository import (
    create_category,
    get_all_categories,
    get_active_categories,
    toggle_category,
)
from repositories.products_repository import (
    create_product,
    get_active_products,
)
from repositories.vehicle_types_repository import (
    create_vehicle_type,
    get_all_vehicle_types,
    get_active_vehicle_types,
    toggle_vehicle_type,
    update_vehicle_type_name,
)
from repositories.vehicles_repository import (
    create_vehicle,
    find_vehicle_by_plate,
    update_vehicle,
)
from repositories.roles_repository import (
    create_role,
    get_all_roles,
    toggle_role,
)
from repositories.role_permissions_repository import (
    get_permissions_for_role,
    set_permissions_for_role,
)
from repositories.users_repository import (
    create_user,
    get_all_users,
    get_user_by_name,
    toggle_user,
    update_user,
    update_user_password,
)
from repositories.incomes_repository import (
    create_income,
    get_incomes,
    get_income_by_id,
    delete_income,
    get_income_total_by_period,
    get_income_grouped_by_service,
    get_income_grouped_by_razon_social,
    get_income_total_by_payment_type,
)
from repositories.services_repository import (
    delete_service,
    get_service_by_id,
    is_service_in_use,
)
from repositories.products_repository import (
    delete_product,
    get_product_by_id,
    is_product_in_use,
)
from repositories.expense_categories_repository import (
    delete_category,
    get_category_by_id,
    is_category_in_use,
)
from repositories.vehicle_types_repository import (
    delete_vehicle_type,
    get_vehicle_type_by_id,
    is_vehicle_type_in_use,
)
from repositories.expenses_repository import create_expense


# =============================================================================
# Serializabilidad de funciones cacheadas (st.cache_data usa pickle)
# =============================================================================

def test_get_active_services_retorna_lista_de_dicts(test_db):
    create_service("Ducha")
    result = get_active_services()
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)


def test_get_active_services_es_serializable(test_db):
    create_service("Aspirado")
    result = get_active_services()
    pickle.dumps(result)  # no debe lanzar excepcion


def test_get_active_products_retorna_lista_de_dicts(test_db):
    create_product("AREON Gel")
    result = get_active_products()
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)


def test_get_active_products_es_serializable(test_db):
    create_product("GEL comun")
    result = get_active_products()
    pickle.dumps(result)


def test_get_active_vehicle_types_retorna_lista_de_dicts(test_db):
    create_vehicle_type("Auto")
    result = get_active_vehicle_types()
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)


def test_get_active_vehicle_types_es_serializable(test_db):
    create_vehicle_type("Moto")
    result = get_active_vehicle_types()
    pickle.dumps(result)


def test_get_active_categories_retorna_lista_de_dicts(test_db):
    create_category("Combustible")
    result = get_active_categories()
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)


def test_get_active_categories_es_serializable(test_db):
    create_category("Insumos")
    result = get_active_categories()
    pickle.dumps(result)


# =============================================================================
# Servicios
# =============================================================================

def test_crear_y_listar_servicio(test_db):
    create_service("Lavado completo")
    services = get_all_services()
    assert any(s["name"] == "Lavado completo" for s in services)


def test_servicio_duplicado_lanza_error(test_db):
    create_service("Lavado")
    with pytest.raises(sqlite3.IntegrityError):
        create_service("Lavado")


def test_get_service_by_id(test_db):
    sid = create_service("Pulido")
    service = get_service_by_id(sid)
    assert service["name"] == "Pulido"
    assert service["is_active"] == 1


def test_get_service_by_id_inexistente(test_db):
    assert get_service_by_id(9999) is None


def test_toggle_desactiva_y_reactiva_servicio(test_db):
    sid = create_service("Encerado")
    toggle_service(sid)
    assert get_service_by_id(sid)["is_active"] == 0
    toggle_service(sid)
    assert get_service_by_id(sid)["is_active"] == 1


def test_get_active_services_excluye_inactivos(test_db):
    sid = create_service("Inactivo")
    toggle_service(sid)
    activos = get_active_services()
    assert not any(s["name"] == "Inactivo" for s in activos)


def test_update_service_name(test_db):
    sid = create_service("Viejo")
    update_service_name(sid, "Nuevo")
    assert get_service_by_id(sid)["name"] == "Nuevo"


# =============================================================================
# Categorias de egreso
# =============================================================================

def test_crear_y_listar_categoria(test_db):
    create_category("Combustible")
    cats = get_all_categories()
    assert any(c["name"] == "Combustible" for c in cats)


def test_categoria_duplicada_lanza_error(test_db):
    create_category("Insumos")
    with pytest.raises(sqlite3.IntegrityError):
        create_category("Insumos")


def test_toggle_categoria(test_db):
    cid = create_category("Alquiler")
    toggle_category(cid)
    cats = get_all_categories()
    cat = next(c for c in cats if c["id"] == cid)
    assert cat["is_active"] == 0


# =============================================================================
# Tipos de vehiculo
# =============================================================================

def test_crear_y_listar_tipo_vehiculo(test_db):
    create_vehicle_type("Auto")
    tipos = get_all_vehicle_types()
    assert any(t["name"] == "Auto" for t in tipos)


def test_tipo_vehiculo_duplicado_lanza_error(test_db):
    create_vehicle_type("Camioneta")
    with pytest.raises(sqlite3.IntegrityError):
        create_vehicle_type("Camioneta")


def test_get_active_vehicle_types(test_db):
    tid = create_vehicle_type("Moto")
    toggle_vehicle_type(tid)
    activos = get_active_vehicle_types()
    assert not any(t["name"] == "Moto" for t in activos)


def test_update_vehicle_type_name(test_db):
    tid = create_vehicle_type("Viejo tipo")
    update_vehicle_type_name(tid, "Nuevo tipo")
    activos = get_all_vehicle_types()
    assert any(t["name"] == "Nuevo tipo" for t in activos)


# =============================================================================
# Vehiculos
# =============================================================================

def test_crear_y_buscar_vehiculo(test_db):
    vt_id = create_vehicle_type("Auto")
    create_vehicle("ABC123", vt_id, "Juan", "0981000000")
    found = find_vehicle_by_plate("ABC123")
    assert found is not None
    assert found["license_plate"] == "ABC123"
    assert found["owner_name"] == "Juan"
    assert found["phone"] == "0981000000"


def test_busqueda_case_insensitive(test_db):
    vt_id = create_vehicle_type("Camioneta")
    create_vehicle("XYZ789", vt_id)
    assert find_vehicle_by_plate("xyz789") is not None
    assert find_vehicle_by_plate("XYZ789") is not None


def test_vehiculo_no_encontrado(test_db):
    assert find_vehicle_by_plate("NOEXISTE") is None


def test_vehiculo_sin_owner(test_db):
    vt_id = create_vehicle_type("Moto")
    vid = create_vehicle("MOT001", vt_id)
    found = find_vehicle_by_plate("MOT001")
    assert found["owner_name"] is None
    assert found["phone"] is None


def test_update_vehiculo(test_db):
    vt1 = create_vehicle_type("Auto2")
    vt2 = create_vehicle_type("Camion")
    vid = create_vehicle("UPD001", vt1, "Viejo", "000")
    update_vehicle(vid, vt2, "Nuevo", "999")
    found = find_vehicle_by_plate("UPD001")
    assert found["owner_name"] == "Nuevo"
    assert found["phone"] == "999"
    assert found["vehicle_type_id"] == vt2


# =============================================================================
# Roles y permisos
# =============================================================================

def test_crear_y_listar_rol(test_db):
    create_role("supervisor")
    roles = get_all_roles()
    assert any(r["name"] == "supervisor" for r in roles)


def test_rol_duplicado_lanza_error(test_db):
    create_role("cajero")
    with pytest.raises(sqlite3.IntegrityError):
        create_role("cajero")


def test_toggle_rol(test_db):
    rid = create_role("temporal")
    toggle_role(rid)
    roles = get_all_roles()
    rol = next(r for r in roles if r["id"] == rid)
    assert rol["is_active"] == 0


def test_set_y_get_permisos(test_db):
    create_role("gerente")
    set_permissions_for_role("gerente", ["dashboard", "export"])
    perms = get_permissions_for_role("gerente")
    assert "dashboard" in perms
    assert "export" in perms


def test_set_permisos_reemplaza_anteriores(test_db):
    create_role("auditor")
    set_permissions_for_role("auditor", ["dashboard", "export"])
    set_permissions_for_role("auditor", ["movements"])
    perms = get_permissions_for_role("auditor")
    assert perms == ["movements"]


def test_get_permisos_rol_sin_permisos(test_db):
    create_role("sin_permisos")
    assert get_permissions_for_role("sin_permisos") == []


# =============================================================================
# Usuarios
# =============================================================================

def test_crear_y_obtener_usuario(test_db):
    create_role("operador")
    create_user("Maria", "operador", "salt:hash")
    user = get_user_by_name("Maria")
    assert user is not None
    assert user["role"] == "operador"
    assert user["is_active"] == 1
    assert user["password_hash"] == "salt:hash"


def test_get_user_no_encontrado(test_db):
    assert get_user_by_name("noexiste") is None


def test_listar_usuarios(test_db):
    create_role("dueno")
    create_user("Pedro", "dueno", "h:a")
    users = get_all_users()
    assert any(u["name"] == "Pedro" for u in users)


def test_toggle_usuario(test_db):
    create_role("rol_test")
    uid = create_user("Carlos", "rol_test", "h:b")
    toggle_user(uid)
    assert get_user_by_name("Carlos")["is_active"] == 0
    toggle_user(uid)
    assert get_user_by_name("Carlos")["is_active"] == 1


def test_update_usuario(test_db):
    create_role("rol_a")
    create_role("rol_b")
    uid = create_user("Ana", "rol_a", "h:c")
    update_user(uid, "Ana Maria", "rol_b")
    user = get_user_by_name("Ana Maria")
    assert user is not None
    assert user["role"] == "rol_b"


def test_update_user_password(test_db):
    create_role("rol_pw")
    uid = create_user("Luis", "rol_pw", "viejo:hash")
    update_user_password(uid, "nuevo:hash")
    user = get_user_by_name("Luis")
    assert user["password_hash"] == "nuevo:hash"


# =============================================================================
# Ingresos
# =============================================================================

def test_crear_y_obtener_ingreso(test_db):
    sid = create_service("Servicio test")
    inc_id = create_income("2026-01-15", sid, 100000, "Efectivo", None, None, "2026-01-15 10:00:00")
    income = get_income_by_id(inc_id)
    assert income["amount"] == 100000
    assert income["service"] == "Servicio test"
    assert income["payment_method"] == "Efectivo"


def test_ingreso_con_vehiculo(test_db):
    sid = create_service("Lavado VIP")
    vt_id = create_vehicle_type("Auto VIP")
    vid = create_vehicle("VIP001", vt_id, "Cliente VIP", None)
    inc_id = create_income("2026-01-15", sid, 200000, None, None, vid, "2026-01-15 11:00:00")
    income = get_income_by_id(inc_id)
    assert income["license_plate"] == "VIP001"
    assert income["vehicle_type"] == "Auto VIP"
    assert income["owner_name"] == "Cliente VIP"


def test_listar_ingresos(test_db):
    sid = create_service("Servicio lista")
    create_income("2026-02-01", sid, 50000, None, None, None, "2026-02-01 09:00:00")
    create_income("2026-02-02", sid, 60000, None, None, None, "2026-02-02 09:00:00")
    ingresos = get_incomes()
    assert len(ingresos) >= 2


def test_filtrar_ingresos_por_fecha(test_db):
    sid = create_service("Filtrado")
    create_income("2026-03-01", sid, 10000, None, None, None, "2026-03-01 10:00:00")
    create_income("2026-04-01", sid, 20000, None, None, None, "2026-04-01 10:00:00")
    marzo = get_incomes("2026-03-01", "2026-03-31")
    assert len(marzo) == 1
    assert marzo[0]["amount"] == 10000


def test_total_ingresos_por_periodo(test_db):
    sid = create_service("Total test")
    create_income("2026-01-10", sid, 50000, None, None, None, "2026-01-10 10:00:00")
    create_income("2026-01-20", sid, 30000, None, None, None, "2026-01-20 10:00:00")
    total = get_income_total_by_period("2026-01-01", "2026-01-31")
    assert total == 80000


def test_total_sin_ingresos(test_db):
    assert get_income_total_by_period("2030-01-01", "2030-01-31") == 0


def test_ingresos_agrupados_por_servicio(test_db):
    sid1 = create_service("Servicio A")
    sid2 = create_service("Servicio B")
    create_income("2026-01-01", sid1, 40000, None, None, None, "2026-01-01 10:00:00")
    create_income("2026-01-01", sid1, 60000, None, None, None, "2026-01-01 11:00:00")
    create_income("2026-01-01", sid2, 20000, None, None, None, "2026-01-01 12:00:00")
    grupos = get_income_grouped_by_service("2026-01-01", "2026-01-31")
    totales = {g["name"]: g["total"] for g in grupos}
    assert totales["Servicio A"] == 100000
    assert totales["Servicio B"] == 20000


def test_eliminar_ingreso(test_db):
    sid = create_service("Para eliminar")
    inc_id = create_income("2026-01-15", sid, 10000, None, None, None, "2026-01-15 10:00:00")
    delete_income(inc_id)
    assert get_income_by_id(inc_id) is None


def test_ingreso_con_payment_type_y_factura(test_db):
    sid = create_service("Servicio factura")
    inc_id = create_income(
        "2026-01-15", sid, 150000, "Transferencia", None, None, "2026-01-15 10:00:00",
        payment_type="Credito", requires_invoice=1, ruc_ci="80012345-6", razon_social="Empresa SA",
    )
    income = get_income_by_id(inc_id)
    assert income["payment_type"] == "Credito"
    assert income["requires_invoice"] == 1
    assert income["ruc_ci"] == "80012345-6"
    assert income["razon_social"] == "Empresa SA"


def test_get_income_total_by_payment_type(test_db):
    sid = create_service("Srv pago tipo")
    create_income("2026-01-01", sid, 100000, None, None, None, "2026-01-01 10:00:00", payment_type="Contado")
    create_income("2026-01-02", sid, 50000, None, None, None, "2026-01-02 10:00:00", payment_type="Credito")
    create_income("2026-01-03", sid, 30000, None, None, None, "2026-01-03 10:00:00", payment_type="Contado")
    totals = get_income_total_by_payment_type("2026-01-01", "2026-01-31")
    assert totals["Contado"] == 130000
    assert totals["Credito"] == 50000


def test_get_income_total_by_payment_type_sin_datos(test_db):
    totals = get_income_total_by_payment_type("2030-01-01", "2030-01-31")
    assert totals == {}


# =============================================================================
# Eliminacion de elementos de catalogo (is_in_use + delete)
# =============================================================================

def test_servicio_no_en_uso_se_puede_eliminar(test_db):
    sid = create_service("Servicio sin usar")
    assert not is_service_in_use(sid)
    delete_service(sid)
    assert get_service_by_id(sid) is None


def test_servicio_en_uso_no_se_puede_borrar_a_nivel_repo(test_db):
    sid = create_service("Servicio con ingreso")
    create_income("2026-01-01", sid, 50000, None, None, None, "2026-01-01 10:00:00")
    assert is_service_in_use(sid)


def test_producto_no_en_uso_se_puede_eliminar(test_db):
    pid = create_product("Producto sin usar")
    assert not is_product_in_use(pid)
    delete_product(pid)
    assert get_product_by_id(pid) is None


def test_producto_en_uso_detectado(test_db):
    sid = create_service("Srv para producto")
    pid = create_product("Producto con venta")
    create_income("2026-01-01", sid, 10000, None, None, None, "2026-01-01 10:00:00", product_id=pid)
    assert is_product_in_use(pid)


def test_categoria_no_en_uso_se_puede_eliminar(test_db):
    cid = create_category("Cat sin usar")
    assert not is_category_in_use(cid)
    delete_category(cid)
    assert get_category_by_id(cid) is None


def test_categoria_en_uso_detectada(test_db):
    cid = create_category("Cat con egreso")
    create_expense("2026-01-01", cid, 30000, None, "2026-01-01 10:00:00")
    assert is_category_in_use(cid)


def test_tipo_vehiculo_no_en_uso_se_puede_eliminar(test_db):
    tid = create_vehicle_type("Tipo sin vehiculos")
    assert not is_vehicle_type_in_use(tid)
    delete_vehicle_type(tid)
    assert get_vehicle_type_by_id(tid) is None


def test_tipo_vehiculo_en_uso_detectado(test_db):
    tid = create_vehicle_type("Tipo con vehiculo")
    create_vehicle("VEH001", tid)
    assert is_vehicle_type_in_use(tid)


# =============================================================================
# get_income_grouped_by_razon_social con income_type
# =============================================================================

def _crear_ingreso_servicio_con_empresa(razon_social, ruc_ci, fecha="2026-01-10"):
    sid = create_service(f"Svc {razon_social}")
    return create_income(
        fecha, sid, 100000, None, None, None, f"{fecha} 10:00:00",
        requires_invoice=1, ruc_ci=ruc_ci, razon_social=razon_social,
    )


def _crear_ingreso_producto_con_empresa(razon_social, ruc_ci, fecha="2026-01-10"):
    pid = create_product(f"Prod {razon_social}")
    return create_income(
        fecha, None, 50000, None, None, None, f"{fecha} 10:00:00",
        requires_invoice=1, ruc_ci=ruc_ci, razon_social=razon_social,
        product_id=pid,
    )


def test_agrupado_por_razon_social_sin_filtro(test_db):
    _crear_ingreso_servicio_con_empresa("Empresa S.A.", "111")
    _crear_ingreso_producto_con_empresa("Empresa S.A.", "111")
    grupos = get_income_grouped_by_razon_social("2026-01-01", "2026-01-31")
    assert len(grupos) == 1
    assert grupos[0]["total"] == 150000


def test_agrupado_por_razon_social_solo_servicios(test_db):
    _crear_ingreso_servicio_con_empresa("Empresa S.R.L.", "222")
    _crear_ingreso_producto_con_empresa("Empresa S.R.L.", "222")
    grupos = get_income_grouped_by_razon_social("2026-01-01", "2026-01-31", income_type="service")
    assert len(grupos) == 1
    assert grupos[0]["total"] == 100000


def test_agrupado_por_razon_social_solo_productos(test_db):
    _crear_ingreso_servicio_con_empresa("Empresa S.A.E.C.A.", "333")
    _crear_ingreso_producto_con_empresa("Empresa S.A.E.C.A.", "333")
    grupos = get_income_grouped_by_razon_social("2026-01-01", "2026-01-31", income_type="product")
    assert len(grupos) == 1
    assert grupos[0]["total"] == 50000


def test_agrupado_por_razon_social_sin_registros_devuelve_lista_vacia(test_db):
    grupos = get_income_grouped_by_razon_social("2026-01-01", "2026-01-31")
    assert grupos == []


def test_agrupado_excluye_ingresos_sin_razon_social(test_db):
    sid = create_service("Svc sin empresa")
    create_income("2026-01-10", sid, 80000, None, None, None, "2026-01-10 10:00:00")
    grupos = get_income_grouped_by_razon_social("2026-01-01", "2026-01-31")
    assert grupos == []
