"""Reglas de negocio para lavanderias de la V2."""

import re

from backend.database.connection import SessionLocal
from backend.repositories.lavanderias_repository import (
    create_lavanderia,
    get_lavanderia_by_id,
    list_lavanderias,
    get_lavanderia_by_subdominio,
    set_lavanderia_status,
    update_lavanderia,
)

SUBDOMINIO_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _normalize_required_text(value, field_label):
    """Valida un texto obligatorio y elimina espacios sobrantes."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"El campo {field_label} es obligatorio.")
    return value.strip()


def _normalize_optional_text(value):
    """Normaliza un texto opcional."""
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    return normalized or None


def _normalize_subdominio(value, field_label="subdominio"):
    """Normaliza un subdominio o host y devuelve solo el subdominio técnico."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"El campo {field_label} es obligatorio.")

    normalized = value.strip().lower()

    if "://" in normalized:
        normalized = normalized.split("://", 1)[1]

    normalized = normalized.split("/", 1)[0]

    if "@" in normalized:
        normalized = normalized.rsplit("@", 1)[1]

    if ":" in normalized:
        normalized = normalized.split(":", 1)[0]

    if "." in normalized:
        normalized = normalized.split(".", 1)[0]

    if not SUBDOMINIO_PATTERN.fullmatch(normalized):
        raise ValueError(
            "El subdominio solo puede contener letras minusculas, numeros y guiones."
        )

    return normalized


def validate_tenant_data(
    nombre_local,
    subdominio,
    nombre_responsable,
    email=None,
    telefono=None,
):
    """Valida y normaliza los datos principales de una lavanderia."""
    return {
        "nombre_local": _normalize_required_text(nombre_local, "nombre_local"),
        "subdominio": _normalize_subdominio(subdominio),
        "nombre_responsable": _normalize_required_text(
            nombre_responsable,
            "nombre_responsable",
        ),
        "email": _normalize_optional_text(email),
        "telefono": _normalize_optional_text(telefono),
    }


def get_all_tenants(only_active=False):
    """Devuelve todas las lavanderias, opcionalmente solo las activas."""
    with SessionLocal() as session:
        return list_lavanderias(session, only_active=only_active)


def get_tenant_by_id(lavanderia_id):
    """Devuelve una lavanderia por id o falla si no existe."""
    with SessionLocal() as session:
        lavanderia = get_lavanderia_by_id(session, lavanderia_id)
        if lavanderia is None:
            raise ValueError("La lavanderia indicada no existe.")
        return lavanderia


def get_tenant_by_subdominio(subdominio):
    """Devuelve una lavanderia por subdominio o falla si no existe."""
    normalized_subdominio = _normalize_subdominio(subdominio)

    with SessionLocal() as session:
        lavanderia = get_lavanderia_by_subdominio(session, normalized_subdominio)
        if lavanderia is None:
            raise ValueError("La lavanderia indicada no existe.")
        return lavanderia


def get_tenant_by_host(host):
    """Resuelve una lavanderia a partir del host o dominio de acceso."""
    normalized_subdominio = _normalize_subdominio(host, field_label="host")
    return get_tenant_by_subdominio(normalized_subdominio)


def register_tenant(
    nombre_local,
    subdominio,
    nombre_responsable,
    email=None,
    telefono=None,
):
    """Valida y crea una nueva lavanderia."""
    validated_data = validate_tenant_data(
        nombre_local,
        subdominio,
        nombre_responsable,
        email=email,
        telefono=telefono,
    )

    with SessionLocal() as session:
        existing = get_lavanderia_by_subdominio(session, validated_data["subdominio"])
        if existing is not None:
            raise ValueError("Ya existe una lavanderia con ese subdominio.")

        lavanderia = create_lavanderia(
            session,
            nombre_local=validated_data["nombre_local"],
            subdominio=validated_data["subdominio"],
            nombre_responsable=validated_data["nombre_responsable"],
            email=validated_data["email"],
            telefono=validated_data["telefono"],
            estado=True,
        )
        session.commit()
        return lavanderia.id


def edit_tenant(
    lavanderia_id,
    nombre_local,
    subdominio,
    nombre_responsable,
    email=None,
    telefono=None,
):
    """Valida y actualiza una lavanderia existente."""
    validated_data = validate_tenant_data(
        nombre_local,
        subdominio,
        nombre_responsable,
        email=email,
        telefono=telefono,
    )

    with SessionLocal() as session:
        lavanderia = get_lavanderia_by_id(session, lavanderia_id)
        if lavanderia is None:
            raise ValueError("La lavanderia indicada no existe.")

        existing = get_lavanderia_by_subdominio(session, validated_data["subdominio"])
        if existing is not None and existing.id != lavanderia.id:
            raise ValueError("Ya existe una lavanderia con ese subdominio.")

        update_lavanderia(
            session,
            lavanderia,
            nombre_local=validated_data["nombre_local"],
            subdominio=validated_data["subdominio"],
            nombre_responsable=validated_data["nombre_responsable"],
            email=validated_data["email"],
            telefono=validated_data["telefono"],
        )
        session.commit()


def toggle_tenant_status(lavanderia_id):
    """Activa o desactiva una lavanderia existente."""
    with SessionLocal() as session:
        lavanderia = get_lavanderia_by_id(session, lavanderia_id)
        if lavanderia is None:
            raise ValueError("La lavanderia indicada no existe.")

        set_lavanderia_status(session, lavanderia, not lavanderia.estado)
        session.commit()
