"""Schemas for sale endpoints."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class SaleItemRequest(BaseModel):
    """Sale detail line request."""

    servicio_id: int | None = None
    producto_id: int | None = None
    cantidad: int = 1
    precio_unitario: float | None = None


class SaleCreateRequest(BaseModel):
    """Create sale request."""

    usuario_id: int | None = None
    fecha_venta: date
    tipo_cobro: str
    items: list[SaleItemRequest] = Field(min_length=1)
    cliente_id: int | None = None
    metodo_pago: str | None = None
    requiere_factura: bool = False
    observacion: str | None = None
    vehiculo_id: int | None = None
    ruc_ci: str | None = None
    razon_social: str | None = None


class SalePaymentTypeRequest(BaseModel):
    """Payment type update request."""

    tipo_cobro: str


class SaleExportRow(BaseModel):
    """Flattened sale row for API listing/export."""

    sale_id: int
    date: date
    payment_type: str
    payment_method: str | None = None
    requires_invoice: bool
    customer_name: str
    ruc_ci: str | None = None
    license_plate: str | None = None
    vehicle_type: str | None = None
    item_type: str
    item: str
    quantity: int
    unit_price: float
    subtotal: float
    sale_total: float
    created_by: str
    notes: str | None = None


class SaleItemResponse(BaseModel):
    """Grouped sale item response."""

    id: int
    item_type: str
    item_name: str
    service_id: int | None = None
    product_id: int | None = None
    quantity: int
    unit_price: float
    subtotal: float


class SaleResponse(BaseModel):
    """Grouped sale response."""

    id: int
    date: date
    created_at: datetime | None = None
    payment_type: str
    payment_method: str | None = None
    requires_invoice: bool
    total: float
    notes: str | None = None
    is_voided: bool = False
    customer_id: int
    customer_name: str
    ruc_ci: str | None = None
    vehicle_id: int | None = None
    license_plate: str | None = None
    vehicle_type_id: int | None = None
    vehicle_type_name: str | None = None
    created_by_user_id: int
    created_by: str
    lavanderia_id: int
    items: list[SaleItemResponse]
