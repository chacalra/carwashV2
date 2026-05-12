"""Acceso a datos de clientes para la V2."""

from sqlalchemy import select

from backend.database.schema import Cliente


def list_clients(session, lavanderia_id, only_active=False):
    """Devuelve clientes de una lavanderia ordenados por nombre."""
    query = (
        select(Cliente)
        .where(Cliente.lavanderia_id == lavanderia_id)
        .order_by(Cliente.nombre.asc(), Cliente.id.asc())
    )

    if only_active:
        query = query.where(Cliente.estado.is_(True))

    return session.scalars(query).all()


def get_client_by_id(session, lavanderia_id, client_id):
    """Busca un cliente por id dentro de una lavanderia."""
    query = select(Cliente).where(
        Cliente.id == client_id,
        Cliente.lavanderia_id == lavanderia_id,
    )
    return session.scalar(query)


def get_client_by_ruc_ci(session, lavanderia_id, ruc_ci):
    """Busca un cliente por documento dentro de una lavanderia."""
    query = select(Cliente).where(
        Cliente.lavanderia_id == lavanderia_id,
        Cliente.ruc_ci == ruc_ci,
    )
    return session.scalar(query)


def get_generic_client(session, lavanderia_id):
    """Devuelve el cliente generico de una lavanderia."""
    query = select(Cliente).where(
        Cliente.lavanderia_id == lavanderia_id,
        Cliente.tipo_cliente == "generico",
    )
    return session.scalar(query)


def create_client(
    session,
    *,
    lavanderia_id,
    nombre,
    tipo_cliente,
    ruc_ci=None,
    telefono=None,
    email=None,
    estado=True,
):
    """Crea un cliente y devuelve la entidad persistida."""
    client = Cliente(
        nombre=nombre,
        tipo_cliente=tipo_cliente,
        ruc_ci=ruc_ci,
        telefono=telefono,
        email=email,
        estado=estado,
        lavanderia_id=lavanderia_id,
    )
    session.add(client)
    session.flush()
    return client


def update_client(
    session,
    client,
    *,
    nombre,
    tipo_cliente,
    ruc_ci=None,
    telefono=None,
    email=None,
):
    """Actualiza los datos principales de un cliente."""
    client.nombre = nombre
    client.tipo_cliente = tipo_cliente
    client.ruc_ci = ruc_ci
    client.telefono = telefono
    client.email = email
    session.flush()
    return client


def set_client_status(session, client, estado):
    """Activa o desactiva un cliente."""
    client.estado = estado
    session.flush()
    return client
