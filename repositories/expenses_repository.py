"""Acceso a datos de egresos."""

from database.connection import get_connection


def create_expense(date, category_id, amount, description, created_at, created_by=None, has_iva=0):
    """Inserta un nuevo egreso y devuelve su id."""
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO expenses (date, category_id, amount, description, created_at, created_by, has_iva)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (date, category_id, amount, description, created_at, created_by, has_iva),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_expenses(start_date=None, end_date=None):
    """Devuelve egresos, opcionalmente filtrados por rango de fechas."""
    connection = get_connection()

    try:
        base_query = """
            SELECT
                expenses.id,
                expenses.date,
                expenses.category_id,
                expense_categories.name AS category,
                expenses.amount,
                expenses.description,
                expenses.has_iva,
                expenses.created_by,
                expenses.created_at
            FROM expenses
            JOIN expense_categories ON expenses.category_id = expense_categories.id
        """

        params = []

        if start_date and end_date:
            base_query += """
                WHERE expenses.date BETWEEN ? AND ?
            """
            params.extend([start_date, end_date])

        base_query += """
            ORDER BY expenses.date DESC, expenses.id DESC;
        """

        rows = connection.execute(base_query, params).fetchall()
        return rows
    finally:
        connection.close()


def get_expense_by_id(expense_id):
    """Busca un egreso por su id."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                expenses.id,
                expenses.date,
                expenses.category_id,
                expense_categories.name AS category,
                expenses.amount,
                expenses.description,
                expenses.has_iva,
                expenses.created_by,
                expenses.created_at
            FROM expenses
            JOIN expense_categories ON expenses.category_id = expense_categories.id
            WHERE expenses.id = ?;
            """,
            (expense_id,),
        ).fetchone()
        return row
    finally:
        connection.close()


def update_expense(expense_id, date, category_id, amount, description, has_iva=0):
    """Actualiza un egreso existente."""
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE expenses
            SET date = ?, category_id = ?, amount = ?, description = ?, has_iva = ?
            WHERE id = ?;
            """,
            (date, category_id, amount, description, has_iva, expense_id),
        )
        connection.commit()
    finally:
        connection.close()


def delete_expense(expense_id):
    """Elimina un egreso por su id."""
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM expenses
            WHERE id = ?;
            """,
            (expense_id,),
        )
        connection.commit()
    finally:
        connection.close()


def get_expense_total_by_period(start_date, end_date):
    """Calcula el total de egresos en un rango de fechas."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE date BETWEEN ? AND ?;
            """,
            (start_date, end_date),
        ).fetchone()
        return row["total"]
    finally:
        connection.close()


def get_expenses_grouped_by_category(start_date, end_date):
    """Agrupa egresos por categoria para un periodo dado."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                expense_categories.name,
                COALESCE(SUM(expenses.amount), 0) AS total
            FROM expenses
            JOIN expense_categories ON expenses.category_id = expense_categories.id
            WHERE expenses.date BETWEEN ? AND ?
            GROUP BY expense_categories.name
            ORDER BY total DESC;
            """,
            (start_date, end_date),
        ).fetchall()
        return rows
    finally:
        connection.close()
