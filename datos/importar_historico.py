"""Script de importacion unica de datos historicos desde ramon MVP.xlsx."""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# --- Configuracion ---
EXCEL_PATH = Path(__file__).parent / "ramon MVP.xlsx"
DB_PATH = Path(__file__).parent.parent / "data" / "carwash.db"

MAPPING = {
    "lavado auto":        {"servicio": "Ducha", "vehiculo": "Auto",                    "matricula": "9999"},
    "lavado camioneta":   {"servicio": "Ducha", "vehiculo": "Camioneta",               "matricula": "9999"},
    "lavado moto":        {"servicio": "Ducha", "vehiculo": "Moto",                    "matricula": "9999"},
    "lavado camioncito":  {"servicio": "Ducha", "vehiculo": "Camioncito",              "matricula": "9999"},
    "lavado alfombra":    {"servicio": "Ducha", "vehiculo": "Auto",                    "matricula": "9999"},
    "alfombra":           {"servicio": "Ducha", "vehiculo": "Auto",                    "matricula": "9999"},
    "areon gel":          {"servicio": "Perfume", "vehiculo": "Mercaderias o productos", "matricula": "0000"},
}


def get_income_rows(df):
    """Extrae filas de ingresos de los tres meses (cols 9-15)."""
    # Rangos por mes (indices de fila en el dataframe)
    rangos = [
        (4,   111),   # Enero
        (114, 197),   # Febrero
        (200, 295),   # Marzo
    ]
    rows = []
    for inicio, fin in rangos:
        bloque = df.iloc[inicio:fin, 9:16].copy()
        bloque.columns = ["fecha", "descripcion", "nro_factura", "cliente", "ruc_ci", "monto", "observaciones"]
        bloque = bloque.dropna(subset=["descripcion", "monto"])
        bloque = bloque[bloque["descripcion"].astype(str).str.strip() != "Descripcion"]
        rows.append(bloque)
    return pd.concat(rows, ignore_index=True)


def find_or_create_vehicle(conn, matricula, vehicle_type_id):
    """Retorna id de vehiculo existente o crea uno nuevo."""
    row = conn.execute(
        "SELECT id FROM vehicles WHERE UPPER(license_plate) = UPPER(?);", (matricula,)
    ).fetchone()
    if row:
        return row[0]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO vehicles (license_plate, vehicle_type_id, created_at) VALUES (?, ?, ?);",
        (matricula, vehicle_type_id, created_at),
    )
    return cur.lastrowid


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    # Cargar IDs de servicios y tipos de vehiculo
    servicios = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM services;")}
    vehiculos = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM vehicle_types;")}

    print("Servicios en DB:", list(servicios.keys()))
    print("Tipos de vehiculo en DB:", list(vehiculos.keys()))

    # Verificar que todos los servicios y vehiculos del mapping existen
    for key, val in MAPPING.items():
        if val["servicio"] not in servicios:
            print(f"ERROR: servicio '{val['servicio']}' no existe en DB")
            sys.exit(1)
        if val["vehiculo"] not in vehiculos:
            print(f"ERROR: tipo de vehiculo '{val['vehiculo']}' no existe en DB")
            sys.exit(1)

    # Leer Excel
    df = pd.read_excel(EXCEL_PATH, sheet_name="INGR-EGRES", header=None)
    ingresos = get_income_rows(df)

    print(f"\nTotal de filas a importar: {len(ingresos)}")

    insertados = 0
    omitidos = 0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in ingresos.iterrows():
        desc = str(row["descripcion"]).strip().lower()
        monto = row["monto"]
        fecha = row["fecha"]

        if desc not in MAPPING:
            print(f"  OMITIDO (sin mapeo): '{row['descripcion']}'")
            omitidos += 1
            continue

        try:
            monto = float(monto)
        except (ValueError, TypeError):
            print(f"  OMITIDO (monto invalido): {monto}")
            omitidos += 1
            continue

        if pd.isna(fecha):
            print(f"  OMITIDO (fecha vacia): {row['descripcion']}")
            omitidos += 1
            continue

        fecha_str = pd.Timestamp(fecha).strftime("%Y-%m-%d")
        m = MAPPING[desc]
        service_id = servicios[m["servicio"]]
        vt_id = vehiculos[m["vehiculo"]]
        vehicle_id = find_or_create_vehicle(conn, m["matricula"], vt_id)

        conn.execute(
            """
            INSERT INTO incomes (
                date, service_id, amount, vehicle_id,
                payment_type, requires_invoice, created_by, created_at
            ) VALUES (?, ?, ?, ?, 'Contado', 0, 'ramon', ?);
            """,
            (fecha_str, service_id, monto, vehicle_id, created_at),
        )
        insertados += 1

    conn.commit()
    conn.close()

    print(f"\n✓ Importados: {insertados}")
    print(f"  Omitidos:   {omitidos}")


# ---------------------------------------------------------------------------
# Facturas de empresas — ramon MVP-2.xlsx / Hoja2
# ---------------------------------------------------------------------------

EXCEL_PATH_2 = Path(__file__).parent / "ramon MVP-2.xlsx"

# Cada bloque = una factura. Cada item = un vehiculo/fila dentro de la factura.
FACTURAS = [
    {
        "date": "2026-04-15",
        "razon_social": "Panaderia La Negrita S.R.L.",
        "ruc_ci": "80002271-8",
        "items": [
            {"vehiculo": "Auto", "matricula": "NEGRITA", "monto": 50000},
            {"vehiculo": "Auto", "matricula": "NEGRITA", "monto": 50000},
        ],
    },
    {
        "date": "2026-03-31",
        "razon_social": "Panaderia La Negrita S.R.L.",
        "ruc_ci": "80002271-8",
        "items": [
            {"vehiculo": "Auto", "matricula": "NEGRITA", "monto": 50000},
            {"vehiculo": "Auto", "matricula": "NEGRITA", "monto": 50000},
            {"vehiculo": "Auto", "matricula": "NEGRITA", "monto": 50000},
        ],
    },
    {
        "date": "2026-03-31",
        "razon_social": "INTERPAN S.A.",
        "ruc_ci": "80062317-7",
        "items": (
            [{"vehiculo": "Camion pequeño", "matricula": "INTERPAN-C", "monto": 100000}] * 8 +
            [{"vehiculo": "Camion pequeño", "matricula": "INTERPAN-C", "monto": 85000}] * 13 +
            [{"vehiculo": "Auto",           "matricula": "INTERPAN-A", "monto": 50000}] * 3
        ),
    },
    {
        "date": "2026-04-15",
        "razon_social": "INTERPAN S.A.",
        "ruc_ci": "80062317-7",
        "items": (
            [{"vehiculo": "Camion pequeño", "matricula": "INTERPAN-C", "monto": 100000}] * 8 +
            [{"vehiculo": "Camion pequeño", "matricula": "INTERPAN-C", "monto": 85000}] * 4 +
            [{"vehiculo": "Auto",           "matricula": "INTERPAN-A", "monto": 50000}] * 1
        ),
    },
]


def importar_facturas_empresas():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    servicios = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM services;")}
    vehiculos = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM vehicle_types;")}

    service_id = servicios.get("Ducha y aspirado")
    if not service_id:
        print("ERROR: servicio 'Ducha y aspirado' no existe en DB")
        conn.close()
        sys.exit(1)

    insertados = 0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for factura in FACTURAS:
        total_factura = sum(i["monto"] for i in factura["items"])
        print(f"\nFactura {factura['razon_social']} {factura['date']} — Gs. {total_factura:,.0f} ({len(factura['items'])} registros)")

        for item in factura["items"]:
            vt_id = vehiculos.get(item["vehiculo"])
            if not vt_id:
                print(f"  ERROR: tipo de vehiculo '{item['vehiculo']}' no existe en DB")
                conn.close()
                sys.exit(1)

            vehicle_id = find_or_create_vehicle(conn, item["matricula"], vt_id)

            conn.execute(
                """
                INSERT INTO incomes (
                    date, service_id, amount, vehicle_id,
                    payment_type, requires_invoice, ruc_ci, razon_social,
                    created_by, created_at
                ) VALUES (?, ?, ?, ?, 'Contado', 1, ?, ?, 'ramon', ?);
                """,
                (
                    factura["date"], service_id, item["monto"], vehicle_id,
                    factura["ruc_ci"], factura["razon_social"], created_at,
                ),
            )
            insertados += 1

    conn.commit()
    conn.close()
    print(f"\n✓ Total insertados: {insertados}")


EXCEL_PATH_3 = Path(__file__).parent / "ramon MVP-3.xlsx"


def reimportar_faltantes():
    """Borra registros historicos con matricula 9999/0000 de ene-mar 2026 y los reimporta
    desde ramon MVP-3.xlsx / FALTANTES POR EDITAR con el servicio/producto correcto.
    created_by = 'ramon' para identificar que fueron cargados manualmente por scripts.
    """
    import pandas as pd

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    servicios = {r["name"].lower(): r["id"] for r in conn.execute("SELECT id, name FROM services;")}
    productos = {r["name"].lower(): r["id"] for r in conn.execute("SELECT id, name FROM products;")}
    vehiculos = {r["name"].lower(): r["id"] for r in conn.execute("SELECT id, name FROM vehicle_types;")}

    # --- Borrar registros historicos con matricula 9999/0000, ene-mar 2026 ---
    cur = conn.execute("""
        DELETE FROM incomes
        WHERE vehicle_id IN (
            SELECT id FROM vehicles WHERE license_plate IN ('9999', '0000')
        )
        AND date BETWEEN '2026-01-01' AND '2026-03-31'
    """)
    borrados = cur.rowcount
    print(f"Registros borrados: {borrados}")

    # --- Leer Excel nuevo ---
    df = pd.read_excel(EXCEL_PATH_3, sheet_name="FALTANTES POR EDITAR", header=None)
    data = df[df[1].notna() & df[1].astype(str).str.strip().isin(["Servicio", "Producto"])].copy()
    data.columns = ["fecha", "tipo", "nombre", "tipo_vehiculo", "monto", "extra"]

    insertados = 0
    omitidos = 0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in data.iterrows():
        fecha = pd.Timestamp(row["fecha"]).strftime("%Y-%m-%d")
        tipo = str(row["tipo"]).strip()
        nombre = str(row["nombre"]).strip()
        monto = float(row["monto"])

        if tipo == "Producto":
            product_id = productos.get(nombre.lower())
            if not product_id:
                print(f"  OMITIDO (producto no encontrado): '{nombre}'")
                omitidos += 1
                continue
            vt_id = vehiculos["mercaderias o productos"]
            vehicle_id = find_or_create_vehicle(conn, "0000", vt_id)
            conn.execute("""
                INSERT INTO incomes (date, product_id, amount, vehicle_id, payment_type,
                    requires_invoice, created_by, created_at)
                VALUES (?, ?, ?, ?, 'Contado', 0, 'ramon', ?)
            """, (fecha, product_id, monto, vehicle_id, created_at))

        else:  # Servicio
            service_id = servicios.get(nombre.lower())
            if not service_id:
                print(f"  OMITIDO (servicio no encontrado): '{nombre}'")
                omitidos += 1
                continue
            tipo_veh = str(row["tipo_vehiculo"]).strip() if pd.notna(row["tipo_vehiculo"]) else "Auto"
            vt_id = vehiculos.get(tipo_veh.lower())
            if not vt_id:
                print(f"  OMITIDO (tipo vehiculo no encontrado): '{tipo_veh}'")
                omitidos += 1
                continue
            vehicle_id = find_or_create_vehicle(conn, "9999", vt_id)
            conn.execute("""
                INSERT INTO incomes (date, service_id, amount, vehicle_id, payment_type,
                    requires_invoice, created_by, created_at)
                VALUES (?, ?, ?, ?, 'Contado', 0, 'ramon', ?)
            """, (fecha, service_id, monto, vehicle_id, created_at))

        insertados += 1

    conn.commit()
    conn.close()
    print(f"✓ Insertados: {insertados}")
    print(f"  Omitidos:   {omitidos}")


NOMBRE_ALIAS = {
    "areon hoja dry": "areon hojas dry",
    "ducha y aspirado": "ducha y aspirado",
}


def importar_faltantes_abril():
    """Importa registros de abril 2026 desde ramon MVP-3.xlsx / FALTANTES POR CARGAR.
    created_by = 'ramon'.
    """
    import pandas as pd

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    servicios = {r["name"].lower(): r["id"] for r in conn.execute("SELECT id, name FROM services;")}
    productos = {r["name"].lower(): r["id"] for r in conn.execute("SELECT id, name FROM products;")}
    vehiculos = {r["name"].lower(): r["id"] for r in conn.execute("SELECT id, name FROM vehicle_types;")}

    df = pd.read_excel(EXCEL_PATH_3, sheet_name="FALTANTES POR CARGAR", header=None)
    data = df[df[1].notna() & df[1].astype(str).str.strip().isin(["Servicio", "Producto"])].copy()
    data.columns = ["fecha", "tipo", "nombre", "tipo_vehiculo", "monto", "extra"]

    insertados = 0
    omitidos = 0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in data.iterrows():
        fecha = pd.Timestamp(row["fecha"]).strftime("%Y-%m-%d")
        tipo = str(row["tipo"]).strip()
        nombre_raw = str(row["nombre"]).strip().lower()
        nombre = NOMBRE_ALIAS.get(nombre_raw, nombre_raw)
        monto = float(row["monto"])

        if tipo == "Producto":
            product_id = productos.get(nombre)
            if not product_id:
                print(f"  OMITIDO (producto no encontrado): '{row['nombre']}'")
                omitidos += 1
                continue
            vt_id = vehiculos["mercaderias o productos"]
            vehicle_id = find_or_create_vehicle(conn, "0000", vt_id)
            conn.execute("""
                INSERT INTO incomes (date, product_id, amount, vehicle_id, payment_type,
                    requires_invoice, created_by, created_at)
                VALUES (?, ?, ?, ?, 'Contado', 0, 'ramon', ?)
            """, (fecha, product_id, monto, vehicle_id, created_at))

        else:
            service_id = servicios.get(nombre)
            if not service_id:
                print(f"  OMITIDO (servicio no encontrado): '{row['nombre']}'")
                omitidos += 1
                continue
            tipo_veh = str(row["tipo_vehiculo"]).strip().lower() if pd.notna(row["tipo_vehiculo"]) else "auto"
            vt_id = vehiculos.get(tipo_veh)
            if not vt_id:
                print(f"  OMITIDO (tipo vehiculo no encontrado): '{row['tipo_vehiculo']}'")
                omitidos += 1
                continue
            vehicle_id = find_or_create_vehicle(conn, "9999", vt_id)
            conn.execute("""
                INSERT INTO incomes (date, service_id, amount, vehicle_id, payment_type,
                    requires_invoice, created_by, created_at)
                VALUES (?, ?, ?, ?, 'Contado', 0, 'ramon', ?)
            """, (fecha, service_id, monto, vehicle_id, created_at))

        insertados += 1

    conn.commit()
    conn.close()
    print(f"✓ Insertados: {insertados}")
    print(f"  Omitidos:   {omitidos}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--facturas", action="store_true", help="Importar facturas de empresas (MVP-2.xlsx)")
    parser.add_argument("--faltantes", action="store_true", help="Reimportar historico corregido (MVP-3.xlsx)")
    parser.add_argument("--abril", action="store_true", help="Importar faltantes de abril 2026 (MVP-3.xlsx)")
    args = parser.parse_args()

    if args.facturas:
        importar_facturas_empresas()
    elif args.faltantes:
        reimportar_faltantes()
    elif args.abril:
        importar_faltantes_abril()
    else:
        main()
