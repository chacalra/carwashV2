"""Reglas de negocio para ingresos."""

from datetime import datetime

from repositories.incomes_repository import (
    create_income,
    delete_income,
    get_razon_social_by_ruc_ci,
    update_income,
)
from utils.formatters import normalize_razon_social
from repositories.products_repository import get_product_by_id
from repositories.services_repository import get_service_by_id
from services.vehicle_service import find_or_create_vehicle, normalize_plate

VALID_PAYMENT_TYPES = ("Contado", "Credito")


def validate_income_data(
    date, service_id, amount, payment_method, notes,
    payment_type="Contado", requires_invoice=False, ruc_ci=None, razon_social=None,
    product_id=None,
):
    """Valida y normaliza los datos de un ingreso."""
    normalized_date = date.strip() if isinstance(date, str) else ""
    normalized_payment_method = (
        payment_method.strip()
        if isinstance(payment_method, str) and payment_method.strip()
        else None
    )
    normalized_notes = notes.strip() if isinstance(notes, str) else None
    normalized_payment_type = (payment_type or "Contado").strip()
    normalized_ruc_ci = ruc_ci.strip() if isinstance(ruc_ci, str) and ruc_ci.strip() else None
    _raw_razon_social = razon_social.strip() if isinstance(razon_social, str) and razon_social.strip() else None
    normalized_razon_social = normalize_razon_social(_raw_razon_social) if _raw_razon_social else None

    if not normalized_date:
        raise ValueError("La fecha del ingreso es obligatoria.")

    if service_id is None and product_id is None:
        raise ValueError("Se debe seleccionar un servicio o producto.")

    if service_id is not None:
        service = get_service_by_id(service_id)
        if service is None:
            raise ValueError("El servicio seleccionado no existe.")
        if service["is_active"] != 1:
            raise ValueError("No se puede registrar un ingreso con un servicio inactivo.")

    if product_id is not None:
        product = get_product_by_id(product_id)
        if product is None:
            raise ValueError("El producto seleccionado no existe.")
        if product["is_active"] != 1:
            raise ValueError("No se puede registrar un ingreso con un producto inactivo.")

    if amount is None or amount <= 0:
        raise ValueError("El monto del ingreso debe ser mayor que cero.")

    if normalized_payment_type not in VALID_PAYMENT_TYPES:
        raise ValueError("El tipo de cobro debe ser Contado o Credito.")

    if requires_invoice:
        if not normalized_ruc_ci:
            raise ValueError("El RUC/CI es obligatorio cuando se genera factura.")
        if not normalized_razon_social:
            raise ValueError("La razon social es obligatoria cuando se genera factura.")
        existing_razon_social = get_razon_social_by_ruc_ci(normalized_ruc_ci)
        if existing_razon_social:
            normalized_razon_social = existing_razon_social

    return {
        "date": normalized_date,
        "service_id": service_id,
        "product_id": product_id,
        "amount": amount,
        "payment_method": normalized_payment_method,
        "notes": normalized_notes,
        "payment_type": normalized_payment_type,
        "requires_invoice": 1 if requires_invoice else 0,
        "ruc_ci": normalized_ruc_ci,
        "razon_social": normalized_razon_social,
    }


def register_income(
    date,
    service_id=None,
    amount=None,
    payment_method=None,
    notes=None,
    license_plate=None,
    vehicle_type_id=None,
    owner_name=None,
    phone=None,
    payment_type="Contado",
    requires_invoice=False,
    ruc_ci=None,
    razon_social=None,
    created_by=None,
    product_id=None,
):
    """Valida y registra un nuevo ingreso, opcionalmente asociado a un vehiculo o producto."""
    validated_data = validate_income_data(
        date, service_id, amount, payment_method, notes,
        payment_type, requires_invoice, ruc_ci, razon_social,
        product_id=product_id,
    )

    vehicle_id = None
    if license_plate and license_plate.strip():
        if not vehicle_type_id:
            raise ValueError("El tipo de vehiculo es obligatorio cuando se indica la matricula.")
        vehicle_id = find_or_create_vehicle(
            normalize_plate(license_plate),
            vehicle_type_id,
            owner_name,
            phone,
        )

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return create_income(
        validated_data["date"],
        validated_data["service_id"],
        validated_data["amount"],
        validated_data["payment_method"],
        validated_data["notes"],
        vehicle_id,
        created_at,
        payment_type=validated_data["payment_type"],
        requires_invoice=validated_data["requires_invoice"],
        ruc_ci=validated_data["ruc_ci"],
        razon_social=validated_data["razon_social"],
        created_by=created_by,
        product_id=validated_data["product_id"],
    )


def edit_income(
    income_id,
    date,
    service_id=None,
    amount=None,
    payment_method=None,
    notes=None,
    license_plate=None,
    vehicle_type_id=None,
    owner_name=None,
    phone=None,
    payment_type="Contado",
    requires_invoice=False,
    ruc_ci=None,
    razon_social=None,
    product_id=None,
):
    """Valida y actualiza un ingreso existente."""
    validated_data = validate_income_data(
        date, service_id, amount, payment_method, notes,
        payment_type, requires_invoice, ruc_ci, razon_social,
        product_id=product_id,
    )

    vehicle_id = None
    if license_plate and license_plate.strip():
        if not vehicle_type_id:
            raise ValueError("El tipo de vehiculo es obligatorio cuando se indica la matricula.")
        vehicle_id = find_or_create_vehicle(
            normalize_plate(license_plate),
            vehicle_type_id,
            owner_name,
            phone,
        )

    update_income(
        income_id,
        validated_data["date"],
        validated_data["service_id"],
        validated_data["amount"],
        validated_data["payment_method"],
        validated_data["notes"],
        vehicle_id,
        payment_type=validated_data["payment_type"],
        requires_invoice=validated_data["requires_invoice"],
        ruc_ci=validated_data["ruc_ci"],
        razon_social=validated_data["razon_social"],
        product_id=validated_data["product_id"],
    )


def remove_income(income_id):
    """Elimina un ingreso existente."""
    delete_income(income_id)
