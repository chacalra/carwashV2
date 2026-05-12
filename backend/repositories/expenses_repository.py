"""Acceso a datos de egresos para la V2."""

from datetime import date as date_type

from sqlalchemy import func, select

from backend.database.connection import SessionLocal
from backend.database.schema import CategoriaEgreso, Egreso, Usuario
from backend.utils.tenant_context import resolve_lavanderia_id


def _parse_date_like(value):
    """Convierte strings YYYY-MM-DD u objetos date a un date real."""
    if isinstance(value, date_type):
        return value
    if isinstance(value, str):
        return date_type.fromisoformat(value.strip())
    raise ValueError("La fecha indicada no es valida.")


def _serialize_expense(expense, category=None, user=None):
    """Convierte una entidad Egreso a un diccionario compatible con UI/reportes."""
    return {
        "id": expense.id,
        "date": expense.fecha,
        "fecha": expense.fecha,
        "category_id": expense.categoria_egreso_id,
        "categoria_egreso_id": expense.categoria_egreso_id,
        "category": category.nombre_categoria if category is not None else None,
        "amount": float(expense.monto),
        "monto": float(expense.monto),
        "description": expense.descripcion,
        "descripcion": expense.descripcion,
        "has_iva": 0,
        "created_by": user.nombre_usuario if user is not None else None,
        "user_id": expense.usuario_id,
        "usuario_id": expense.usuario_id,
        "created_at": expense.created_at,
        "lavanderia_id": expense.lavanderia_id,
        "estado": expense.estado,
    }


def _resolve_user(session, lavanderia_id, *, user_id=None, created_by=None):
    """Resuelve el usuario del egreso dentro de la lavanderia actual."""
    if user_id is not None:
        query = select(Usuario).where(
            Usuario.id == user_id,
            Usuario.lavanderia_id == lavanderia_id,
        )
        user = session.scalar(query)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        return user

    if isinstance(created_by, str) and created_by.strip():
        query = select(Usuario).where(
            Usuario.nombre_usuario == created_by.strip(),
            Usuario.lavanderia_id == lavanderia_id,
        )
        user = session.scalar(query)
        if user is None:
            raise ValueError("El usuario indicado no existe.")
        return user

    raise ValueError("Hace falta indicar el usuario que registra el egreso.")


def create_expense(
    session,
    date,
    category_id,
    amount,
    description,
    created_at=None,
    created_by=None,
    has_iva=0,
    *,
    lavanderia_id=None,
    user_id=None,
):
    """Inserta un nuevo egreso y devuelve su id."""
    del created_at, has_iva
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    expense_date = _parse_date_like(date)

    category_query = select(CategoriaEgreso).where(
        CategoriaEgreso.id == category_id,
        CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
    )
    category = session.scalar(category_query)
    if category is None:
        raise ValueError("La categoria indicada no existe.")

    user = _resolve_user(
        session,
        resolved_lavanderia_id,
        user_id=user_id,
        created_by=created_by,
    )

    expense = Egreso(
        fecha=expense_date,
        monto=amount,
        descripcion=description,
        estado=True,
        lavanderia_id=resolved_lavanderia_id,
        categoria_egreso_id=category.id,
        usuario_id=user.id,
    )
    session.add(expense)
    session.flush()
    return expense.id


def get_expenses(start_date=None, end_date=None, lavanderia_id=None):
    """Devuelve egresos activos, opcionalmente filtrados por rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(Egreso, CategoriaEgreso, Usuario)
            .join(CategoriaEgreso, CategoriaEgreso.id == Egreso.categoria_egreso_id)
            .join(Usuario, Usuario.id == Egreso.usuario_id)
            .where(
                Egreso.lavanderia_id == resolved_lavanderia_id,
                Egreso.estado.is_(True),
            )
        )

        if start_date and end_date:
            query = query.where(
                Egreso.fecha.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                )
            )

        rows = session.execute(
            query.order_by(Egreso.fecha.desc(), Egreso.id.desc())
        ).all()
        return [
            _serialize_expense(expense, category, user)
            for expense, category, user in rows
        ]


def get_expense_by_id(expense_id, lavanderia_id=None):
    """Busca un egreso por su id dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(Egreso, CategoriaEgreso, Usuario)
            .join(CategoriaEgreso, CategoriaEgreso.id == Egreso.categoria_egreso_id)
            .join(Usuario, Usuario.id == Egreso.usuario_id)
            .where(
                Egreso.id == expense_id,
                Egreso.lavanderia_id == resolved_lavanderia_id,
            )
        )
        row = session.execute(query).first()
        if row is None:
            return None

        expense, category, user = row
        return _serialize_expense(expense, category, user)


def update_expense(
    session,
    expense_id,
    date,
    category_id,
    amount,
    description,
    has_iva=0,
    *,
    lavanderia_id=None,
):
    """Actualiza un egreso existente."""
    del has_iva
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)
    expense_date = _parse_date_like(date)

    expense_query = select(Egreso).where(
        Egreso.id == expense_id,
        Egreso.lavanderia_id == resolved_lavanderia_id,
    )
    expense = session.scalar(expense_query)
    if expense is None:
        raise ValueError("El egreso indicado no existe.")
    if not expense.estado:
        raise ValueError("El egreso indicado ya fue anulado.")

    category_query = select(CategoriaEgreso).where(
        CategoriaEgreso.id == category_id,
        CategoriaEgreso.lavanderia_id == resolved_lavanderia_id,
    )
    category = session.scalar(category_query)
    if category is None:
        raise ValueError("La categoria indicada no existe.")

    expense.fecha = expense_date
    expense.categoria_egreso_id = category.id
    expense.monto = amount
    expense.descripcion = description
    session.flush()


def cancel_expense(session, expense_id, lavanderia_id=None):
    """Anula logicamente un egreso por su id dentro del tenant actual."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    query = select(Egreso).where(
        Egreso.id == expense_id,
        Egreso.lavanderia_id == resolved_lavanderia_id,
    )
    expense = session.scalar(query)
    if expense is None:
        raise ValueError("El egreso indicado no existe.")
    if not expense.estado:
        raise ValueError("El egreso indicado ya fue anulado.")

    expense.estado = False
    session.flush()


def get_expense_total_by_period(start_date, end_date, lavanderia_id=None):
    """Calcula el total de egresos activos en un rango de fechas."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = select(func.coalesce(func.sum(Egreso.monto), 0)).where(
            Egreso.lavanderia_id == resolved_lavanderia_id,
            Egreso.estado.is_(True),
            Egreso.fecha.between(
                _parse_date_like(start_date),
                _parse_date_like(end_date),
            ),
        )
        total = session.scalar(query)
        return float(total or 0)


def get_expenses_grouped_by_category(start_date, end_date, lavanderia_id=None):
    """Agrupa egresos activos por categoria para un periodo dado."""
    resolved_lavanderia_id = resolve_lavanderia_id(lavanderia_id, required=True)

    with SessionLocal() as session:
        query = (
            select(
                CategoriaEgreso.nombre_categoria.label("name"),
                func.coalesce(func.sum(Egreso.monto), 0).label("total"),
            )
            .join(CategoriaEgreso, CategoriaEgreso.id == Egreso.categoria_egreso_id)
            .where(
                Egreso.lavanderia_id == resolved_lavanderia_id,
                Egreso.estado.is_(True),
                Egreso.fecha.between(
                    _parse_date_like(start_date),
                    _parse_date_like(end_date),
                ),
            )
            .group_by(CategoriaEgreso.nombre_categoria)
            .order_by(func.sum(Egreso.monto).desc())
        )
        rows = session.execute(query).all()
        return [{"name": name, "total": float(total)} for name, total in rows]
