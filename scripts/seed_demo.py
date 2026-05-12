"""Pobla el tenant `demo` con datos representativos para demos comerciales.

Uso:
  uv run python scripts/seed_demo.py [--subdomain demo] [--reset]

Que hace:
  - Verifica que el tenant exista (creado con create-tenant antes).
  - Crea cliente generico "Sin nombre" si no existe.
  - Carga catalogos genericos: tipos vehiculo, servicios, productos, categorias egreso.
  - Genera ~30 ventas + 10 egresos repartidos en los ultimos 30 dias.
  - Distribucion de ventas: 70% solo servicio + matricula, 20% mezcla
    servicio + producto, 10% solo productos sin matricula.
  - ~20% de ventas con factura (RUC/razon social ficticios).

Idempotencia: si el tenant ya tiene ventas, no hace nada (a menos que se
pase --reset, que borra ventas/egresos antes de sembrar de nuevo).

Datos NO realistas pero verosimiles: las matriculas siguen patrones
paraguayos (ABC123, AAA001), los clientes tienen nombres falsos.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, delete

from backend.database.connection import SessionLocal
from backend.database.schema import (
    CategoriaEgreso,
    Cliente,
    DetalleVenta,
    Egreso,
    Lavanderia,
    Producto,
    Rol,
    Servicio,
    TipoVehiculo,
    Usuario,
    Vehiculo,
    Venta,
)


# Semilla fija para que cada corrida produzca los mismos datos.
# Hace la demo predecible (util si la mostras a la misma persona dos veces).
random.seed(42)


# --- catalogo generico de lavadero ---

VEHICLE_TYPES = ["Auto", "Camioneta", "Camion pequeño", "Moto"]

SERVICES = [
    ("Lavado basico", 30000),
    ("Lavado premium", 50000),
    ("Aspirado", 15000),
    ("Encerado", 70000),
    ("Lavado de tapizado", 80000),
]

PRODUCTS = [
    ("Cera liquida", 25000),
    ("Perfume colgante", 15000),
    ("Microfibra", 18000),
    ("Shampoo automotor", 35000),
    ("Aromatizante spray", 12000),
    ("Limpiavidrios", 20000),
]

EXPENSE_CATEGORIES = [
    "Insumos",
    "Sueldos",
    "Servicios basicos",
    "Mantenimiento",
    "Otros",
]

# Empresas ficticias para las ventas con factura (~20% del total).
INVOICE_CUSTOMERS = [
    ("AutoFlota Demo SA", "80012345-1"),
    ("Distribuidora Norte SRL", "80098765-2"),
    ("Transportes del Sur", "80055544-3"),
]

# Pool de matriculas. Mezcla formato viejo (ABC123) y nuevo (AAAA000).
PLATES = [
    "ABC123", "DEF456", "GHI789", "JKL012", "MNO345", "PQR678",
    "AAAA001", "BBBB002", "CCCC003", "DDDD004", "EEEE005", "FFFF006",
    "GGGG007", "HHHH008", "IIII009", "JJJJ010",
]


# --- helpers ---

def _get_tenant_or_exit(session, subdomain):
    lav = session.scalar(select(Lavanderia).where(Lavanderia.subdominio == subdomain))
    if lav is None:
        sys.exit(
            f"No existe tenant '{subdomain}'. Crealo primero con create-tenant."
        )
    return lav


def _get_admin_user(session, lavanderia_id):
    admin_role = session.scalar(
        select(Rol).where(Rol.lavanderia_id == lavanderia_id, Rol.nombre == "admin")
    )
    if admin_role is None:
        sys.exit("El tenant no tiene rol 'admin'. Recrealo con create-tenant.")
    user = session.scalar(
        select(Usuario)
        .where(Usuario.lavanderia_id == lavanderia_id, Usuario.rol_id == admin_role.id)
        .order_by(Usuario.id.asc())
    )
    if user is None:
        sys.exit("El tenant no tiene usuario admin.")
    return user


def _reset_data(session, lavanderia_id):
    """Borra ventas, detalles, egresos del tenant. Conserva catalogos y usuarios."""
    venta_ids = session.scalars(
        select(Venta.id).where(Venta.lavanderia_id == lavanderia_id)
    ).all()
    if venta_ids:
        session.execute(delete(DetalleVenta).where(DetalleVenta.venta_id.in_(venta_ids)))
        session.execute(delete(Venta).where(Venta.id.in_(venta_ids)))
    session.execute(delete(Egreso).where(Egreso.lavanderia_id == lavanderia_id))
    session.flush()


def _ensure_generic_client(session, lavanderia_id):
    existing = session.scalar(
        select(Cliente).where(
            Cliente.lavanderia_id == lavanderia_id,
            Cliente.tipo_cliente == "generico",
        )
    )
    if existing is not None:
        return existing
    cliente = Cliente(
        nombre="Sin nombre",
        tipo_cliente="generico",
        estado=True,
        lavanderia_id=lavanderia_id,
    )
    session.add(cliente)
    session.flush()
    return cliente


def _seed_catalogs(session, lavanderia_id):
    """Inserta catalogos solo si estan vacios. Devuelve mappings nombre->id."""
    types_map = {}
    for name in VEHICLE_TYPES:
        existing = session.scalar(
            select(TipoVehiculo).where(
                TipoVehiculo.lavanderia_id == lavanderia_id,
                TipoVehiculo.nombre == name,
            )
        )
        if existing is None:
            t = TipoVehiculo(nombre=name, estado=True, lavanderia_id=lavanderia_id)
            session.add(t)
            session.flush()
            existing = t
        types_map[name] = existing

    services_map = {}
    for name, price in SERVICES:
        existing = session.scalar(
            select(Servicio).where(
                Servicio.lavanderia_id == lavanderia_id,
                Servicio.nombre_servicio == name,
            )
        )
        if existing is None:
            s = Servicio(
                nombre_servicio=name,
                precio=Decimal(str(price)),
                estado=True,
                lavanderia_id=lavanderia_id,
            )
            session.add(s)
            session.flush()
            existing = s
        services_map[name] = existing

    products_map = {}
    for name, price in PRODUCTS:
        existing = session.scalar(
            select(Producto).where(
                Producto.lavanderia_id == lavanderia_id,
                Producto.nombre_producto == name,
            )
        )
        if existing is None:
            p = Producto(
                nombre_producto=name,
                precio=Decimal(str(price)),
                estado=True,
                lavanderia_id=lavanderia_id,
            )
            session.add(p)
            session.flush()
            existing = p
        products_map[name] = existing

    categories_map = {}
    for name in EXPENSE_CATEGORIES:
        existing = session.scalar(
            select(CategoriaEgreso).where(
                CategoriaEgreso.lavanderia_id == lavanderia_id,
                CategoriaEgreso.nombre_categoria == name,
            )
        )
        if existing is None:
            c = CategoriaEgreso(
                nombre_categoria=name, estado=True, lavanderia_id=lavanderia_id
            )
            session.add(c)
            session.flush()
            existing = c
        categories_map[name] = existing

    return types_map, services_map, products_map, categories_map


def _ensure_vehicles(session, lavanderia_id, types_map):
    """Crea (idempotente) los vehiculos del pool. Devuelve dict plate -> Vehiculo."""
    out = {}
    for plate in PLATES:
        existing = session.scalar(
            select(Vehiculo).where(
                Vehiculo.lavanderia_id == lavanderia_id,
                Vehiculo.matricula == plate,
            )
        )
        if existing is None:
            t = random.choice(list(types_map.values()))
            v = Vehiculo(
                matricula=plate,
                tipo_vehiculo_id=t.id,
                cliente_id=None,
                estado=True,
                lavanderia_id=lavanderia_id,
            )
            session.add(v)
            session.flush()
            existing = v
        out[plate] = existing
    return out


def _ensure_invoice_clients(session, lavanderia_id):
    """Upsert de los clientes con factura."""
    out = []
    for name, ruc in INVOICE_CUSTOMERS:
        existing = session.scalar(
            select(Cliente).where(
                Cliente.lavanderia_id == lavanderia_id,
                Cliente.ruc_ci == ruc,
            )
        )
        if existing is None:
            c = Cliente(
                nombre=name,
                tipo_cliente="particular",
                ruc_ci=ruc,
                estado=True,
                lavanderia_id=lavanderia_id,
            )
            session.add(c)
            session.flush()
            existing = c
        out.append(existing)
    return out


# --- generacion de ventas y egresos ---

PAYMENT_METHODS = ["Efectivo", "Transferencia", "Tarjeta", "QR"]


def _random_date_within(days_back=30):
    """Fecha random uniforme en los ultimos `days_back` dias."""
    offset = random.randint(0, days_back - 1)
    return date.today() - timedelta(days=offset)


def _generate_sales(
    session,
    lavanderia_id,
    admin_user,
    generic_client,
    invoice_clients,
    services_map,
    products_map,
    vehicles_map,
    target_count=30,
):
    """Genera ~target_count ventas con la distribucion definida."""
    services = list(services_map.values())
    products = list(products_map.values())
    vehicles = list(vehicles_map.values())

    for _ in range(target_count):
        # Decidir tipo de venta segun distribucion.
        roll = random.random()
        if roll < 0.10:
            # 10% solo productos sin vehiculo
            items_def = [(None, random.choice(products), random.randint(1, 3))]
            vehiculo = None
        elif roll < 0.30:
            # 20% mezcla servicio + 1-2 productos, con vehiculo
            servicio = random.choice(services)
            n_prods = random.randint(1, 2)
            chosen_prods = random.sample(products, k=min(n_prods, len(products)))
            items_def = [(servicio, None, 1)]
            for p in chosen_prods:
                items_def.append((None, p, random.randint(1, 2)))
            vehiculo = random.choice(vehicles)
        else:
            # 70% solo servicio con matricula
            servicio = random.choice(services)
            items_def = [(servicio, None, 1)]
            vehiculo = random.choice(vehicles)

        # Factura: ~20% de las ventas. Solo permitido si la venta tiene un
        # cliente identificable (los 3 fijos del pool).
        requires_invoice = random.random() < 0.20
        if requires_invoice:
            cliente = random.choice(invoice_clients)
        else:
            cliente = generic_client

        fecha = _random_date_within(30)
        metodo = random.choices(
            PAYMENT_METHODS, weights=[60, 25, 10, 5]
        )[0]
        tipo_cobro = "Credito" if requires_invoice and random.random() < 0.3 else "Contado"

        # Crear venta + detalles. Calcular total.
        total = Decimal("0")
        details_to_add = []
        for srv, prod, qty in items_def:
            unit_price = srv.precio if srv else prod.precio
            subtotal = unit_price * qty
            total += subtotal
            details_to_add.append({
                "cantidad": qty,
                "precio_unitario": unit_price,
                "subtotal": subtotal,
                "servicio_id": srv.id if srv else None,
                "producto_id": prod.id if prod else None,
            })

        venta = Venta(
            fecha_venta=fecha,
            tipo_cobro=tipo_cobro,
            metodo_pago=metodo,
            requiere_factura=requires_invoice,
            total=total,
            observacion=None,
            cliente_id=cliente.id,
            lavanderia_id=lavanderia_id,
            usuario_id=admin_user.id,
            vehiculo_id=vehiculo.id if vehiculo else None,
            estado=True,
        )
        session.add(venta)
        session.flush()

        for d in details_to_add:
            session.add(DetalleVenta(venta_id=venta.id, **d))
    session.flush()


def _generate_expenses(
    session, lavanderia_id, admin_user, categories_map, target_count=10
):
    """Genera ~target_count egresos con montos verosimiles por categoria."""
    # Rangos tipicos por categoria (Gs.).
    ranges = {
        "Insumos": (15000, 80000),
        "Sueldos": (300000, 800000),
        "Servicios basicos": (40000, 200000),
        "Mantenimiento": (20000, 150000),
        "Otros": (10000, 50000),
    }
    cats_list = list(categories_map.items())
    for _ in range(target_count):
        cat_name, cat = random.choice(cats_list)
        low, high = ranges.get(cat_name, (10000, 100000))
        monto = Decimal(str(random.randint(low, high)))
        fecha = _random_date_within(30)
        eg = Egreso(
            fecha=fecha,
            monto=monto,
            descripcion=None,
            estado=True,
            lavanderia_id=lavanderia_id,
            categoria_egreso_id=cat.id,
            usuario_id=admin_user.id,
        )
        session.add(eg)
    session.flush()


# --- entry ---

def run(*, subdomain, reset):
    with SessionLocal() as session:
        lav = _get_tenant_or_exit(session, subdomain)
        admin = _get_admin_user(session, lav.id)

        # Idempotencia: si ya hay ventas y no se pidio reset, no tocamos.
        existing_sales = session.scalar(
            select(Venta.id).where(Venta.lavanderia_id == lav.id).limit(1)
        )
        if existing_sales is not None and not reset:
            print(
                f"El tenant '{subdomain}' ya tiene ventas. "
                f"Usa --reset si queres borrarlas y resembrar. Salgo sin tocar."
            )
            return 0

        if reset and existing_sales is not None:
            print("→ --reset: borrando ventas y egresos previos...")
            _reset_data(session, lav.id)

        print("→ Cliente generico...")
        generic = _ensure_generic_client(session, lav.id)

        print("→ Catalogos...")
        types_map, services_map, products_map, categories_map = _seed_catalogs(
            session, lav.id
        )

        print("→ Vehiculos del pool...")
        vehicles_map = _ensure_vehicles(session, lav.id, types_map)

        print("→ Clientes con factura...")
        invoice_clients = _ensure_invoice_clients(session, lav.id)

        print("→ Generando ~30 ventas (ultimos 30 dias)...")
        _generate_sales(
            session,
            lavanderia_id=lav.id,
            admin_user=admin,
            generic_client=generic,
            invoice_clients=invoice_clients,
            services_map=services_map,
            products_map=products_map,
            vehicles_map=vehicles_map,
            target_count=30,
        )

        print("→ Generando ~10 egresos...")
        _generate_expenses(
            session,
            lavanderia_id=lav.id,
            admin_user=admin,
            categories_map=categories_map,
            target_count=10,
        )

        session.commit()
        print(f"✓ Tenant '{subdomain}' poblado con datos demo.")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="seed_demo")
    parser.add_argument("--subdomain", default="demo")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra ventas y egresos previos antes de sembrar. Cuidado.",
    )
    args = parser.parse_args(argv)
    return run(subdomain=args.subdomain, reset=args.reset)


if __name__ == "__main__":
    sys.exit(main())
