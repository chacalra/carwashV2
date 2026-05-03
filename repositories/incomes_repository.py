"""Acceso a datos de ingresos."""

from database.connection import get_connection


def create_income(
    date, service_id, amount, payment_method, notes, vehicle_id, created_at,
    payment_type="Contado", requires_invoice=0, ruc_ci=None, razon_social=None,
    created_by=None, product_id=None,
):
    """Inserta un nuevo ingreso y devuelve su id."""
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO incomes (
                date, service_id, amount, payment_method, notes, vehicle_id, created_at,
                payment_type, requires_invoice, ruc_ci, razon_social, created_by, product_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                date, service_id, amount, payment_method, notes, vehicle_id, created_at,
                payment_type, requires_invoice, ruc_ci, razon_social, created_by, product_id,
            ),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_incomes(start_date=None, end_date=None):
    """Devuelve ingresos, opcionalmente filtrados por rango de fechas."""
    connection = get_connection()

    try:
        base_query = """
            SELECT
                incomes.id,
                incomes.date,
                incomes.service_id,
                incomes.product_id,
                COALESCE(services.name, products.name) AS service,
                vehicles.license_plate,
                vehicle_types.name AS vehicle_type,
                vehicles.owner_name,
                incomes.amount,
                incomes.payment_method,
                incomes.payment_type,
                incomes.requires_invoice,
                incomes.ruc_ci,
                incomes.razon_social,
                incomes.notes,
                incomes.created_by,
                incomes.created_at
            FROM incomes
            LEFT JOIN services ON incomes.service_id = services.id
            LEFT JOIN products ON incomes.product_id = products.id
            LEFT JOIN vehicles ON incomes.vehicle_id = vehicles.id
            LEFT JOIN vehicle_types ON vehicles.vehicle_type_id = vehicle_types.id
        """

        params = []

        if start_date and end_date:
            base_query += """
                WHERE incomes.date BETWEEN ? AND ?
            """
            params.extend([start_date, end_date])

        base_query += """
            ORDER BY incomes.date DESC, incomes.id DESC;
        """

        rows = connection.execute(base_query, params).fetchall()
        return rows
    finally:
        connection.close()


def get_income_by_id(income_id):
    """Busca un ingreso por su id."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                incomes.id,
                incomes.date,
                incomes.service_id,
                incomes.product_id,
                COALESCE(services.name, products.name) AS service,
                incomes.vehicle_id,
                vehicles.license_plate,
                vehicles.vehicle_type_id,
                vehicle_types.name AS vehicle_type,
                vehicles.owner_name,
                vehicles.phone,
                incomes.amount,
                incomes.payment_method,
                incomes.payment_type,
                incomes.requires_invoice,
                incomes.ruc_ci,
                incomes.razon_social,
                incomes.notes,
                incomes.created_by,
                incomes.created_at
            FROM incomes
            LEFT JOIN services ON incomes.service_id = services.id
            LEFT JOIN products ON incomes.product_id = products.id
            LEFT JOIN vehicles ON incomes.vehicle_id = vehicles.id
            LEFT JOIN vehicle_types ON vehicles.vehicle_type_id = vehicle_types.id
            WHERE incomes.id = ?;
            """,
            (income_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def update_income(
    income_id, date, service_id, amount, payment_method, notes, vehicle_id=None,
    payment_type="Contado", requires_invoice=0, ruc_ci=None, razon_social=None,
    product_id=None,
):
    """Actualiza un ingreso existente."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE incomes
            SET date = ?, service_id = ?, amount = ?, payment_method = ?, notes = ?,
                vehicle_id = ?, payment_type = ?, requires_invoice = ?, ruc_ci = ?,
                razon_social = ?, product_id = ?
            WHERE id = ?;
            """,
            (
                date, service_id, amount, payment_method, notes, vehicle_id,
                payment_type, requires_invoice, ruc_ci, razon_social, product_id, income_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def update_income_payment_type(income_id, payment_type):
    """Actualiza solo el tipo de cobro de un ingreso."""
    connection = get_connection()

    try:
        connection.execute(
            "UPDATE incomes SET payment_type = ? WHERE id = ?;",
            (payment_type, income_id),
        )
        connection.commit()
    finally:
        connection.close()


def delete_income(income_id):
    """Elimina un ingreso por su id."""
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM incomes
            WHERE id = ?;
            """,
            (income_id,),
        )
        connection.commit()
    finally:
        connection.close()


def get_last_income_by_vehicle(vehicle_id):
    """Devuelve el ultimo ingreso registrado para un vehiculo dado."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                incomes.service_id,
                services.name AS service,
                incomes.amount,
                incomes.payment_method,
                incomes.payment_type,
                incomes.requires_invoice,
                incomes.ruc_ci,
                incomes.razon_social,
                incomes.notes
            FROM incomes
            JOIN services ON incomes.service_id = services.id
            WHERE incomes.vehicle_id = ?
            ORDER BY incomes.id DESC
            LIMIT 1;
            """,
            (vehicle_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def get_product_stats(start_date, end_date):
    """Devuelve estadisticas de ventas por producto para un periodo."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                products.name,
                COUNT(incomes.id) AS sale_count,
                COALESCE(SUM(incomes.amount), 0) AS total
            FROM incomes
            JOIN products ON incomes.product_id = products.id
            WHERE incomes.date BETWEEN ? AND ?
            GROUP BY products.id
            ORDER BY sale_count DESC;
            """,
            (start_date, end_date),
        ).fetchall()
        return rows
    finally:
        connection.close()


def get_income_count_by_period(start_date, end_date):
    """Cuenta el numero de ingresos de servicios (lavados) en un rango de fechas."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM incomes
            WHERE date BETWEEN ? AND ?
              AND service_id IS NOT NULL;
            """,
            (start_date, end_date),
        ).fetchone()
        return row["count"]
    finally:
        connection.close()


def get_product_count_by_period(start_date, end_date):
    """Cuenta el numero de ventas de productos en un rango de fechas."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM incomes
            WHERE date BETWEEN ? AND ?
              AND product_id IS NOT NULL;
            """,
            (start_date, end_date),
        ).fetchone()
        return row["count"]
    finally:
        connection.close()


def get_income_total_by_period(start_date, end_date):
    """Calcula el total de ingresos en un rango de fechas."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM incomes
            WHERE date BETWEEN ? AND ?;
            """,
            (start_date, end_date),
        ).fetchone()
        return row["total"]
    finally:
        connection.close()


def get_income_grouped_by_service(start_date, end_date):
    """Agrupa ingresos por servicio para un periodo dado."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                COALESCE(services.name, products.name) AS name,
                COUNT(*) AS count,
                COALESCE(SUM(incomes.amount), 0) AS total
            FROM incomes
            LEFT JOIN services ON incomes.service_id = services.id
            LEFT JOIN products ON incomes.product_id = products.id
            WHERE incomes.date BETWEEN ? AND ?
            GROUP BY COALESCE(services.name, products.name)
            ORDER BY total DESC;
            """,
            (start_date, end_date),
        ).fetchall()
        return rows
    finally:
        connection.close()


def get_service_income_total(start_date, end_date):
    """Calcula el total de ingresos de servicios (lavados) en un rango de fechas, excluyendo productos."""
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM incomes
            WHERE date BETWEEN ? AND ?
              AND service_id IS NOT NULL;
            """,
            (start_date, end_date),
        ).fetchone()
        return row["total"]
    finally:
        connection.close()


def get_income_total_by_payment_type(start_date, end_date):
    """Devuelve totales de ingresos separados por tipo de cobro (Contado / Credito)."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT COALESCE(payment_type, 'Contado') AS payment_type, COALESCE(SUM(amount), 0) AS total
            FROM incomes
            WHERE date BETWEEN ? AND ?
            GROUP BY COALESCE(payment_type, 'Contado');
            """,
            (start_date, end_date),
        ).fetchall()
        return {row["payment_type"]: row["total"] for row in rows}
    finally:
        connection.close()


def get_razon_social_by_ruc_ci(ruc_ci):
    """Devuelve la razon_social mas frecuente registrada para un RUC/CI dado, o None si no existe."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT razon_social
            FROM incomes
            WHERE ruc_ci = ? AND razon_social IS NOT NULL
            GROUP BY razon_social
            ORDER BY COUNT(*) DESC
            LIMIT 1;
            """,
            (ruc_ci,),
        ).fetchone()
        return row["razon_social"] if row else None
    finally:
        connection.close()


def get_income_grouped_by_razon_social(start_date, end_date, income_type=None):
    """Devuelve totales de ingresos agrupados por razon social (solo registros con factura).

    income_type: 'service' filtra solo servicios, 'product' solo productos, None ambos.
    """
    connection = get_connection()

    type_filter = ""
    if income_type == "service":
        type_filter = "AND service_id IS NOT NULL"
    elif income_type == "product":
        type_filter = "AND product_id IS NOT NULL"

    try:
        rows = connection.execute(
            f"""
            SELECT
                razon_social,
                ruc_ci,
                COUNT(*) AS count,
                SUM(amount) AS total
            FROM incomes
            WHERE date BETWEEN ? AND ?
              AND razon_social IS NOT NULL
              {type_filter}
            GROUP BY razon_social, ruc_ci
            ORDER BY total DESC;
            """,
            (start_date, end_date),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_income_detail_by_razon_social(start_date, end_date, razon_social):
    """Devuelve detalle de ingresos de una empresa especifica en el periodo."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                i.date,
                COALESCE(s.name, p.name) AS service,
                vt.name AS vehicle_type,
                i.amount
            FROM incomes i
            LEFT JOIN services s ON i.service_id = s.id
            LEFT JOIN products p ON i.product_id = p.id
            LEFT JOIN vehicles v ON i.vehicle_id = v.id
            LEFT JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            WHERE i.date BETWEEN ? AND ?
              AND i.razon_social = ?
            ORDER BY i.date, i.amount DESC;
            """,
            (start_date, end_date, razon_social),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_daily_incomes(start_date, end_date):
    """Devuelve ingresos totales agrupados por dia para el periodo dado."""
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT date, SUM(amount) AS total
            FROM incomes
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date;
            """,
            (start_date, end_date),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_customer_stats(start_date, end_date):
    """Devuelve estadisticas de vehiculos atendidos en un periodo."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                vehicles.license_plate,
                vehicle_types.name AS vehicle_type,
                vehicles.owner_name,
                COUNT(incomes.id) AS visit_count
            FROM incomes
            JOIN vehicles ON incomes.vehicle_id = vehicles.id
            LEFT JOIN vehicle_types ON vehicles.vehicle_type_id = vehicle_types.id
            WHERE incomes.date BETWEEN ? AND ?
              AND vehicles.license_plate NOT IN ('9999', '0000')
            GROUP BY vehicles.id
            ORDER BY visit_count DESC;
            """,
            (start_date, end_date),
        ).fetchall()
        return rows
    finally:
        connection.close()
