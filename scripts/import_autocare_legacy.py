"""Importa el .db SQLite legacy del cliente AutoCare a la base V2.

Uso:
  uv run python -m scripts.import_autocare_legacy \
      --subdomain autocare \
      --db-path datos/autocare_legacy.db \
      [--dry-run]

Que hace, en una sola transaccion:
  - resuelve el tenant `autocare` (lavanderia_id) y su usuario admin
  - crea (si no existe) el cliente generico "Sin nombre" tipo generico
  - importa catalogos: vehicle_types, services (sin "Perfume" basura),
    products, expense_categories
  - importa vehicles excluyendo placeholder "0000" (mantiene "9999"
    como historico de matricula no registrada)
  - importa expenses
  - importa incomes -> ventas + detalle_venta:
      * 1 income = 1 venta con 1 detalle (cantidad=1, precio=amount)
      * vehicle_id == 0000 se descarta (era placeholder de productos)
      * requires_invoice=1 -> upsert cliente particular con razon_social/ruc_ci
      * requires_invoice=0 -> cliente generico "Sin nombre"
  - todos los movimientos atribuidos al admin del tenant

Salta intencionalmente: users, roles, role_permissions, sqlite_sequence.

Si la lavanderia ya tiene movimientos previos, aborta (pedir --force para
importar igual; usar con cuidado, no dedupica).

Precios: importa servicios y productos con precio = 0. Rafael los edita
desde Settings despues.

La regla nueva "vehiculo obligatorio si hay servicio" se aplica via
inserts directos a los repositories, sin pasar por sale_service. Las 363
ventas de servicio con vehicle_id 9999 quedan asociadas a ese vehiculo
(nada de NULL en servicio).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import date as date_cls, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

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


PLACEHOLDER_PRODUCT_PLATE = "0000"
PLACEHOLDER_HISTORIC_PLATE = "9999"
GENERIC_CLIENT_NAME = "Sin nombre"
SKIPPED_SERVICE_NAMES = {"Perfume"}  # servicio basura sin uso en el legacy
ZERO_PRICE = Decimal("0.00")


def _parse_iso_date(value):
    """Convierte 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS' a date."""
    if isinstance(value, date_cls):
        return value
    if not value:
        raise ValueError("fecha vacia")
    raw = str(value).strip()
    # Intenta como datetime primero (legacy a veces guarda con hora).
    for parser in (date_cls.fromisoformat, lambda x: datetime.fromisoformat(x).date()):
        try:
            return parser(raw[:10] if len(raw) > 10 else raw)
        except (ValueError, TypeError):
            continue
    raise ValueError(f"fecha invalida: {raw!r}")


def _open_legacy(db_path):
    """Abre el SQLite legacy en read-only."""
    p = Path(db_path).resolve()
    if not p.exists():
        raise SystemExit(f"No existe el archivo: {p}")
    uri = f"file:{p}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_tenant_and_admin(session, subdomain):
    """Devuelve (lavanderia, admin_usuario). Aborta si falta alguno."""
    lavanderia = session.scalar(
        select(Lavanderia).where(Lavanderia.subdominio == subdomain)
    )
    if lavanderia is None:
        raise SystemExit(
            f"No existe tenant con subdominio {subdomain!r}. "
            f"Creá el tenant primero con `create-tenant`."
        )

    admin_role = session.scalar(
        select(Rol).where(
            Rol.lavanderia_id == lavanderia.id,
            Rol.nombre == "admin",
        )
    )
    if admin_role is None:
        raise SystemExit(f"El tenant {subdomain!r} no tiene rol 'admin'.")

    admin = session.scalar(
        select(Usuario)
        .where(
            Usuario.lavanderia_id == lavanderia.id,
            Usuario.rol_id == admin_role.id,
            Usuario.estado.is_(True),
        )
        .order_by(Usuario.id.asc())
    )
    if admin is None:
        raise SystemExit(
            f"El tenant {subdomain!r} no tiene un usuario admin activo."
        )
    return lavanderia, admin


def _ensure_clean_tenant(session, lavanderia_id, force):
    """Aborta si la lavanderia ya tiene movimientos importados, salvo --force."""
    if force:
        return
    existing_sales = session.scalar(
        select(Venta.id).where(Venta.lavanderia_id == lavanderia_id).limit(1)
    )
    existing_expenses = session.scalar(
        select(Egreso.id).where(Egreso.lavanderia_id == lavanderia_id).limit(1)
    )
    if existing_sales or existing_expenses:
        raise SystemExit(
            "El tenant ya tiene ventas o egresos cargados. "
            "Usa --force si estas seguro (no dedupica)."
        )


def _ensure_generic_client(session, lavanderia_id):
    """Crea o devuelve el cliente generico 'Sin nombre' del tenant."""
    existing = session.scalar(
        select(Cliente).where(
            Cliente.lavanderia_id == lavanderia_id,
            Cliente.tipo_cliente == "generico",
        )
    )
    if existing is not None:
        return existing
    cliente = Cliente(
        nombre=GENERIC_CLIENT_NAME,
        tipo_cliente="generico",
        ruc_ci=None,
        telefono=None,
        email=None,
        estado=True,
        lavanderia_id=lavanderia_id,
    )
    session.add(cliente)
    session.flush()
    return cliente


def _import_vehicle_types(session, legacy, lavanderia_id):
    """legacy.vehicle_types -> tipos_vehiculo. Devuelve {legacy_id: nuevo_id}."""
    mapping = {}
    rows = legacy.execute(
        "SELECT id, name, is_active FROM vehicle_types ORDER BY id"
    ).fetchall()
    for row in rows:
        tipo = TipoVehiculo(
            nombre=row["name"],
            estado=bool(row["is_active"]),
            lavanderia_id=lavanderia_id,
        )
        session.add(tipo)
        session.flush()
        mapping[row["id"]] = tipo.id
    return mapping


def _import_services(session, legacy, lavanderia_id):
    """legacy.services -> servicios. Salta los nombres en SKIPPED_SERVICE_NAMES."""
    mapping = {}
    skipped = 0
    rows = legacy.execute(
        "SELECT id, name, is_active FROM services ORDER BY id"
    ).fetchall()
    for row in rows:
        if row["name"] in SKIPPED_SERVICE_NAMES:
            skipped += 1
            continue
        servicio = Servicio(
            nombre_servicio=row["name"],
            precio=ZERO_PRICE,
            estado=bool(row["is_active"]),
            lavanderia_id=lavanderia_id,
        )
        session.add(servicio)
        session.flush()
        mapping[row["id"]] = servicio.id
    return mapping, skipped


def _import_products(session, legacy, lavanderia_id):
    """legacy.products -> productos."""
    mapping = {}
    rows = legacy.execute(
        "SELECT id, name, is_active FROM products ORDER BY id"
    ).fetchall()
    for row in rows:
        producto = Producto(
            nombre_producto=row["name"],
            precio=ZERO_PRICE,
            estado=bool(row["is_active"]),
            lavanderia_id=lavanderia_id,
        )
        session.add(producto)
        session.flush()
        mapping[row["id"]] = producto.id
    return mapping


def _import_expense_categories(session, legacy, lavanderia_id):
    """legacy.expense_categories -> categorias_egreso."""
    mapping = {}
    rows = legacy.execute(
        "SELECT id, name, is_active FROM expense_categories ORDER BY id"
    ).fetchall()
    for row in rows:
        cat = CategoriaEgreso(
            nombre_categoria=row["name"],
            estado=bool(row["is_active"]),
            lavanderia_id=lavanderia_id,
        )
        session.add(cat)
        session.flush()
        mapping[row["id"]] = cat.id
    return mapping


def _import_vehicles(session, legacy, lavanderia_id, vehicle_type_map):
    """legacy.vehicles -> vehiculos. Excluye matricula '0000' (placeholder)."""
    mapping = {}
    skipped_placeholder = []
    rows = legacy.execute(
        "SELECT id, license_plate, vehicle_type_id FROM vehicles ORDER BY id"
    ).fetchall()
    for row in rows:
        plate = (row["license_plate"] or "").strip()
        if plate == PLACEHOLDER_PRODUCT_PLATE:
            skipped_placeholder.append(row["id"])
            continue
        new_type_id = vehicle_type_map.get(row["vehicle_type_id"])
        if new_type_id is None:
            raise SystemExit(
                f"vehiculo legacy {row['id']} apunta a tipo {row['vehicle_type_id']} no mapeado"
            )
        veh = Vehiculo(
            matricula=plate or None,
            tipo_vehiculo_id=new_type_id,
            cliente_id=None,
            estado=True,
            lavanderia_id=lavanderia_id,
        )
        session.add(veh)
        session.flush()
        mapping[row["id"]] = veh.id
    return mapping, skipped_placeholder


def _import_expenses(session, legacy, lavanderia_id, admin_user_id, category_map):
    """legacy.expenses -> egresos."""
    count = 0
    rows = legacy.execute(
        "SELECT id, date, category_id, amount, description "
        "FROM expenses ORDER BY id"
    ).fetchall()
    for row in rows:
        new_cat = category_map.get(row["category_id"])
        if new_cat is None:
            raise SystemExit(
                f"egreso legacy {row['id']} apunta a categoria {row['category_id']} no mapeada"
            )
        descripcion = (row["description"] or "").strip() or None
        eg = Egreso(
            fecha=_parse_iso_date(row["date"]),
            monto=Decimal(str(row["amount"])),
            descripcion=descripcion,
            estado=True,
            lavanderia_id=lavanderia_id,
            categoria_egreso_id=new_cat,
            usuario_id=admin_user_id,
        )
        session.add(eg)
        count += 1
    session.flush()
    return count


def _resolve_invoice_client(session, lavanderia_id, ruc_ci, razon_social, cache):
    """Upsert de cliente particular con ruc_ci. Cachea en `cache`."""
    key = (ruc_ci or "").strip()
    if key in cache:
        return cache[key]
    existing = session.scalar(
        select(Cliente).where(
            Cliente.lavanderia_id == lavanderia_id,
            Cliente.ruc_ci == key,
        )
    )
    if existing is not None:
        cache[key] = existing
        return existing
    cliente = Cliente(
        nombre=(razon_social or "").strip() or "(sin razon social)",
        tipo_cliente="particular",
        ruc_ci=key,
        telefono=None,
        email=None,
        estado=True,
        lavanderia_id=lavanderia_id,
    )
    session.add(cliente)
    session.flush()
    cache[key] = cliente
    return cliente


def _import_incomes(
    session,
    legacy,
    *,
    lavanderia_id,
    admin_user_id,
    generic_client_id,
    service_map,
    product_map,
    vehicle_map,
):
    """legacy.incomes -> ventas + detalles_venta."""
    invoice_cache = {}
    counts = defaultdict(int)
    rows = legacy.execute(
        "SELECT id, date, service_id, product_id, amount, payment_method, "
        "notes, vehicle_id, payment_type, requires_invoice, ruc_ci, razon_social "
        "FROM incomes ORDER BY id"
    ).fetchall()

    for row in rows:
        # Tipo de detalle
        legacy_service = row["service_id"]
        legacy_product = row["product_id"]
        if legacy_service is None and legacy_product is None:
            raise SystemExit(f"income {row['id']} no tiene service ni product")
        if legacy_service is not None and legacy_product is not None:
            raise SystemExit(f"income {row['id']} tiene service y product a la vez")

        # Vehiculo: si apuntaba al placeholder 0000 (que NO esta en vehicle_map),
        # se descarta. Si apunta a un vehiculo mapeado, lo usamos.
        new_vehicle_id = None
        if row["vehicle_id"] is not None:
            new_vehicle_id = vehicle_map.get(row["vehicle_id"])
            if new_vehicle_id is None:
                # Era el placeholder 0000 (esperado en ventas de producto)
                counts["vehicle_dropped_0000"] += 1

        # Resolver detalle (servicio o producto)
        if legacy_service is not None:
            servicio_id = service_map.get(legacy_service)
            if servicio_id is None:
                # Servicio descartado (ej: "Perfume" sin uso). No deberia pasar.
                raise SystemExit(
                    f"income {row['id']} usa servicio {legacy_service} no mapeado"
                )
            producto_id = None
        else:
            producto_id = product_map.get(legacy_product)
            if producto_id is None:
                raise SystemExit(
                    f"income {row['id']} usa producto {legacy_product} no mapeado"
                )
            servicio_id = None

        # Cliente
        requires_invoice = bool(row["requires_invoice"])
        if requires_invoice and (row["ruc_ci"] or "").strip():
            cliente = _resolve_invoice_client(
                session,
                lavanderia_id,
                row["ruc_ci"],
                row["razon_social"],
                invoice_cache,
            )
            cliente_id = cliente.id
        else:
            cliente_id = generic_client_id

        # Tipo de cobro
        tipo_cobro = (row["payment_type"] or "Contado").strip() or "Contado"
        if tipo_cobro not in ("Contado", "Credito"):
            tipo_cobro = "Contado"

        metodo_pago = (row["payment_method"] or "").strip() or None
        observacion = (row["notes"] or "").strip() or None
        amount = Decimal(str(row["amount"]))

        venta = Venta(
            fecha_venta=_parse_iso_date(row["date"]),
            tipo_cobro=tipo_cobro,
            metodo_pago=metodo_pago,
            requiere_factura=requires_invoice,
            total=amount,
            observacion=observacion,
            cliente_id=cliente_id,
            lavanderia_id=lavanderia_id,
            usuario_id=admin_user_id,
            vehiculo_id=new_vehicle_id,
            estado=True,
        )
        session.add(venta)
        session.flush()

        detalle = DetalleVenta(
            cantidad=1,
            precio_unitario=amount,
            subtotal=amount,
            venta_id=venta.id,
            servicio_id=servicio_id,
            producto_id=producto_id,
        )
        session.add(detalle)

        if servicio_id is not None:
            counts["sales_service"] += 1
        else:
            counts["sales_product"] += 1
        if requires_invoice:
            counts["sales_invoice"] += 1

    session.flush()
    counts["sales_total"] = counts["sales_service"] + counts["sales_product"]
    return dict(counts)


def run(*, subdomain, db_path, dry_run, force):
    legacy = _open_legacy(db_path)
    session = SessionLocal()
    try:
        lavanderia, admin = _resolve_tenant_and_admin(session, subdomain)
        _ensure_clean_tenant(session, lavanderia.id, force)

        generic = _ensure_generic_client(session, lavanderia.id)

        vehicle_type_map = _import_vehicle_types(session, legacy, lavanderia.id)
        service_map, services_skipped = _import_services(session, legacy, lavanderia.id)
        product_map = _import_products(session, legacy, lavanderia.id)
        category_map = _import_expense_categories(session, legacy, lavanderia.id)
        vehicle_map, vehicles_skipped = _import_vehicles(
            session, legacy, lavanderia.id, vehicle_type_map
        )
        expenses_count = _import_expenses(
            session, legacy, lavanderia.id, admin.id, category_map
        )
        income_counts = _import_incomes(
            session,
            legacy,
            lavanderia_id=lavanderia.id,
            admin_user_id=admin.id,
            generic_client_id=generic.id,
            service_map=service_map,
            product_map=product_map,
            vehicle_map=vehicle_map,
        )

        summary = {
            "tenant": subdomain,
            "lavanderia_id": lavanderia.id,
            "admin_user_id": admin.id,
            "generic_client_id": generic.id,
            "vehicle_types": len(vehicle_type_map),
            "services_imported": len(service_map),
            "services_skipped": services_skipped,
            "products": len(product_map),
            "expense_categories": len(category_map),
            "vehicles_imported": len(vehicle_map),
            "vehicles_skipped_placeholder": len(vehicles_skipped),
            "expenses": expenses_count,
            **income_counts,
            "dry_run": dry_run,
        }

        if dry_run:
            session.rollback()
            print("DRY-RUN: rollback hecho. Resumen previsto:")
        else:
            session.commit()
            print("OK: import comiteado. Resumen:")

        for key in sorted(summary.keys()):
            print(f"  {key}: {summary[key]}")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        legacy.close()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="import_autocare_legacy")
    parser.add_argument("--subdomain", required=True)
    parser.add_argument("--db-path", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Hace rollback al final. No persiste nada.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Importa aunque la lavanderia ya tenga movimientos. Sin dedup.",
    )
    args = parser.parse_args(argv)
    return run(
        subdomain=args.subdomain,
        db_path=args.db_path,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main())
