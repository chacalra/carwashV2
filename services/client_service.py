"""Reglas de negocio para clientes de la V2."""

from repositories.clients_repository import (
    create_client,
    get_client_by_id,
    get_client_by_ruc_ci,
    get_generic_client,
    set_client_status,
    update_client,
)
from database.connection import SessionLocal


VALID_CLIENT_TYPES = ("particular", "empresa", "generico")


def _normalize_required_name(nombre):
    """Valida que el nombre exista y elimina espacios sobrantes."""
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre del cliente es obligatorio.")
    return nombre.strip()


def _normalize_client_type(tipo_cliente):
    """Normaliza y valida el tipo de cliente permitido."""
    normalized = (
        tipo_cliente.strip().lower() if isinstance(tipo_cliente, str) else ""
    )
    if normalized not in VALID_CLIENT_TYPES:
        raise ValueError(
            "El tipo de cliente debe ser particular, empresa o generico."
        )
    return normalized


def _normalize_optional_text(value):
    """Normaliza campos de texto opcionales."""
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    return normalized or None


def validate_client_data(nombre, tipo_cliente, ruc_ci=None, telefono=None, email=None):
    """Valida y normaliza los datos de un cliente."""
    normalized_name = _normalize_required_name(nombre)
    normalized_type = _normalize_client_type(tipo_cliente)
    normalized_ruc_ci = _normalize_optional_text(ruc_ci)
    normalized_phone = _normalize_optional_text(telefono)
    normalized_email = _normalize_optional_text(email)

    return {
        "nombre": normalized_name,
        "tipo_cliente": normalized_type,
        "ruc_ci": normalized_ruc_ci,
        "telefono": normalized_phone,
        "email": normalized_email,
    }


def register_client(
    lavanderia_id,
    nombre,
    tipo_cliente,
    ruc_ci=None,
    telefono=None,
    email=None,
):
    """Valida y crea un cliente nuevo dentro de una lavanderia."""
    validated_data = validate_client_data(
        nombre,
        tipo_cliente,
        ruc_ci=ruc_ci,
        telefono=telefono,
        email=email,
    )

    with SessionLocal() as session:
        if validated_data["ruc_ci"] is not None:
            existing = get_client_by_ruc_ci(
                session,
                lavanderia_id,
                validated_data["ruc_ci"],
            )
            if existing is not None:
                raise ValueError(
                    "Ya existe un cliente con ese RUC/CI en esta lavanderia."
                )

        client = create_client(
            session,
            lavanderia_id=lavanderia_id,
            nombre=validated_data["nombre"],
            tipo_cliente=validated_data["tipo_cliente"],
            ruc_ci=validated_data["ruc_ci"],
            telefono=validated_data["telefono"],
            email=validated_data["email"],
            estado=True,
        )
        session.commit()
        return client.id


def edit_client(
    lavanderia_id,
    client_id,
    nombre,
    tipo_cliente,
    ruc_ci=None,
    telefono=None,
    email=None,
):
    """Valida y actualiza un cliente existente."""
    validated_data = validate_client_data(
        nombre,
        tipo_cliente,
        ruc_ci=ruc_ci,
        telefono=telefono,
        email=email,
    )

    with SessionLocal() as session:
        client = get_client_by_id(session, lavanderia_id, client_id)
        if client is None:
            raise ValueError("El cliente indicado no existe en esta lavanderia.")

        if validated_data["ruc_ci"] is not None:
            existing = get_client_by_ruc_ci(
                session,
                lavanderia_id,
                validated_data["ruc_ci"],
            )
            if existing is not None and existing.id != client_id:
                raise ValueError(
                    "Ya existe otro cliente con ese RUC/CI en esta lavanderia."
                )

        update_client(
            session,
            client,
            nombre=validated_data["nombre"],
            tipo_cliente=validated_data["tipo_cliente"],
            ruc_ci=validated_data["ruc_ci"],
            telefono=validated_data["telefono"],
            email=validated_data["email"],
        )
        session.commit()


def toggle_client_status(lavanderia_id, client_id):
    """Activa o desactiva un cliente existente."""
    with SessionLocal() as session:
        client = get_client_by_id(session, lavanderia_id, client_id)
        if client is None:
            raise ValueError("El cliente indicado no existe en esta lavanderia.")

        set_client_status(session, client, not client.estado)
        session.commit()


def ensure_generic_client(lavanderia_id):
    """Devuelve el cliente generico o falla si no existe en la lavanderia."""
    with SessionLocal() as session:
        client = get_generic_client(session, lavanderia_id)
        if client is None:
            raise ValueError(
                "No existe un cliente generico configurado para esta lavanderia."
            )
        return client
