"""Creacion del esquema SQLite del proyecto."""

from database.connection import get_connection


def create_vehicle_types_table(connection):
    """Crea la tabla de catalogo de tipos de vehiculo."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            CHECK (trim(name) <> ''),
            CHECK (is_active IN (0, 1)),
            CHECK (trim(created_at) <> '')
        );
        """
    )


def create_vehicles_table(connection):
    """Crea la tabla de vehiculos registrados."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL UNIQUE,
            vehicle_type_id INTEGER NOT NULL,
            owner_name TEXT,
            phone TEXT,
            created_at TEXT NOT NULL,
            CHECK (trim(license_plate) <> ''),
            CHECK (trim(created_at) <> ''),
            FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(id)
        );
        """
    )


def create_roles_table(connection):
    """Crea la tabla de roles del sistema."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            CHECK (trim(name) <> ''),
            CHECK (is_active IN (0, 1)),
            CHECK (trim(created_at) <> '')
        );
        """
    )


def create_role_permissions_table(connection):
    """Crea la tabla de permisos por rol."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL,
            permission TEXT NOT NULL,
            UNIQUE (role_name, permission)
        );
        """
    )


def create_users_table(connection):
    """Crea la tabla de usuarios del sistema (sin CHECK en role para roles dinamicos)."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operador',
            password_hash TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            CHECK (trim(name) <> ''),
            CHECK (is_active IN (0, 1)),
            CHECK (trim(created_at) <> '')
        );
        """
    )


def create_products_table(connection):
    """Crea la tabla de catalogo de productos."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            CHECK (trim(name) <> ''),
            CHECK (is_active IN (0, 1)),
            CHECK (trim(created_at) <> '')
        );
        """
    )


def create_services_table(connection):
    """Crea la tabla de catalogo de servicios."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            CHECK (trim(name) <> ''),
            CHECK (is_active IN (0, 1)),
            CHECK (trim(created_at) <> '')
        );
        """
    )


def create_expense_categories_table(connection):
    """Crea la tabla de categorias de egreso."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            CHECK (trim(name) <> ''),
            CHECK (is_active IN (0, 1)),
            CHECK (trim(created_at) <> '')
        );
        """
    )


def create_incomes_table(connection):
    """Crea la tabla de ingresos."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            service_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            CHECK (trim(date) <> ''),
            CHECK (amount > 0),
            CHECK (payment_method IS NULL OR trim(payment_method) <> ''),
            CHECK (trim(created_at) <> ''),
            FOREIGN KEY (service_id) REFERENCES services(id)
        );
        """
    )


def create_expenses_table(connection):
    """Crea la tabla de egresos."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            CHECK (trim(date) <> ''),
            CHECK (amount > 0),
            CHECK (description IS NULL OR trim(description) <> ''),
            CHECK (trim(created_at) <> ''),
            FOREIGN KEY (category_id) REFERENCES expense_categories(id)
        );
        """
    )


def migrate_v2(connection):
    """Agrega columna vehicle_id a incomes si no existe."""
    columns = [
        row[1]
        for row in connection.execute("PRAGMA table_info(incomes)").fetchall()
    ]
    if "vehicle_id" not in columns:
        connection.execute(
            "ALTER TABLE incomes ADD COLUMN vehicle_id INTEGER REFERENCES vehicles(id);"
        )


def migrate_v3(connection):
    """Agrega columnas payment_type, requires_invoice, ruc_ci, razon_social a incomes."""
    columns = [
        row[1]
        for row in connection.execute("PRAGMA table_info(incomes)").fetchall()
    ]
    migrations = [
        ("payment_type", "ALTER TABLE incomes ADD COLUMN payment_type TEXT DEFAULT 'Contado';"),
        ("requires_invoice", "ALTER TABLE incomes ADD COLUMN requires_invoice INTEGER DEFAULT 0;"),
        ("ruc_ci", "ALTER TABLE incomes ADD COLUMN ruc_ci TEXT;"),
        ("razon_social", "ALTER TABLE incomes ADD COLUMN razon_social TEXT;"),
    ]
    for col, sql in migrations:
        if col not in columns:
            connection.execute(sql)


def migrate_v4(connection):
    """Agrega columna created_by a incomes y expenses para trazabilidad."""
    income_cols = [row[1] for row in connection.execute("PRAGMA table_info(incomes)").fetchall()]
    if "created_by" not in income_cols:
        connection.execute("ALTER TABLE incomes ADD COLUMN created_by TEXT;")

    expense_cols = [row[1] for row in connection.execute("PRAGMA table_info(expenses)").fetchall()]
    if "created_by" not in expense_cols:
        connection.execute("ALTER TABLE expenses ADD COLUMN created_by TEXT;")


def migrate_v5(connection):
    """Agrega columna has_iva a expenses."""
    columns = [row[1] for row in connection.execute("PRAGMA table_info(expenses)").fetchall()]
    if "has_iva" not in columns:
        connection.execute("ALTER TABLE expenses ADD COLUMN has_iva INTEGER DEFAULT 0;")


def migrate_v6(connection):
    """Crea tabla products y agrega product_id a incomes (hace service_id nullable)."""
    # La tabla products se crea en create_products_table; aqui solo agregamos product_id a incomes
    columns = [row[1] for row in connection.execute("PRAGMA table_info(incomes)").fetchall()]
    if "product_id" not in columns:
        # Recrear incomes con service_id nullable y columna product_id nueva
        connection.execute("ALTER TABLE incomes RENAME TO incomes_old;")
        connection.execute(
            """
            CREATE TABLE incomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                service_id INTEGER,
                amount REAL NOT NULL,
                payment_method TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                vehicle_id INTEGER,
                payment_type TEXT DEFAULT 'Contado',
                requires_invoice INTEGER DEFAULT 0,
                ruc_ci TEXT,
                razon_social TEXT,
                created_by TEXT,
                product_id INTEGER,
                CHECK (trim(date) <> ''),
                CHECK (amount > 0),
                CHECK (payment_method IS NULL OR trim(payment_method) <> ''),
                CHECK (trim(created_at) <> ''),
                CHECK (service_id IS NOT NULL OR product_id IS NOT NULL),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )
        connection.execute(
            """
            INSERT INTO incomes (
                id, date, service_id, amount, payment_method, notes, created_at,
                vehicle_id, payment_type, requires_invoice, ruc_ci, razon_social,
                created_by, product_id
            )
            SELECT
                id, date, service_id, amount, payment_method, notes, created_at,
                vehicle_id, payment_type, requires_invoice, ruc_ci, razon_social,
                created_by, NULL
            FROM incomes_old;
            """
        )
        connection.execute("DROP TABLE incomes_old;")


def migrate_users_auth(connection):
    """
    Recrea la tabla users para agregar password_hash y eliminar el CHECK
    de role (para permitir roles dinamicos). Solo corre si falta password_hash.
    """
    columns = [
        row[1]
        for row in connection.execute("PRAGMA table_info(users)").fetchall()
    ]
    if "password_hash" not in columns:
        connection.execute("ALTER TABLE users RENAME TO users_old;")
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operador',
                password_hash TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                CHECK (trim(name) <> ''),
                CHECK (is_active IN (0, 1)),
                CHECK (trim(created_at) <> '')
            );
            """
        )
        connection.execute(
            """
            INSERT INTO users (id, name, role, password_hash, is_active, created_at)
            SELECT id, name, role, NULL, is_active, created_at FROM users_old;
            """
        )
        connection.execute("DROP TABLE users_old;")


def create_tables():
    """Crea todas las tablas necesarias del sistema."""
    connection = get_connection()

    try:
        create_vehicle_types_table(connection)
        create_vehicles_table(connection)
        create_roles_table(connection)
        create_role_permissions_table(connection)
        create_users_table(connection)
        create_services_table(connection)
        create_products_table(connection)
        create_expense_categories_table(connection)
        create_incomes_table(connection)
        create_expenses_table(connection)
        migrate_v2(connection)
        migrate_v3(connection)
        migrate_v4(connection)
        migrate_v5(connection)
        migrate_v6(connection)
        migrate_users_auth(connection)
        connection.commit()
    finally:
        connection.close()
