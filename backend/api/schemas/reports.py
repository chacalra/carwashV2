"""Schemas for report endpoints."""

from pydantic import BaseModel


class BreakdownItem(BaseModel):
    """Breakdown row."""

    name: str
    count: int | None = None
    total: float


class PaymentBreakdown(BaseModel):
    """Payment breakdown values."""

    contado: float
    credito: float


class DailySalesItem(BaseModel):
    """Daily sales row for trend charts."""

    date: str
    total: float


class SalesSummaryResponse(BaseModel):
    """Sales summary response."""

    start_date: str
    end_date: str
    sales_total: float
    expense_total: float
    net_balance: float
    service_count: int
    service_sales_total: float
    product_count: int
    sales_breakdown: list[BreakdownItem]
    expense_breakdown: list[BreakdownItem]
    payment_breakdown: PaymentBreakdown


class TopPlateItem(BaseModel):
    """Top customer/vehicle row from get_vehicle_sales_stats."""

    license_plate: str | None = None
    vehicle_type: str | None = None
    owner_name: str | None = None
    visit_count: int


class CustomerSummaryResponse(BaseModel):
    """Customer/vehicle stats for a period."""

    unique_vehicles: int
    recurring_customers: int
    new_customers: int
    top_plates: list[TopPlateItem]


class TopProductItem(BaseModel):
    """Top product row from get_product_sales_stats."""

    name: str
    sale_count: int
    total: float


class ProductSummaryResponse(BaseModel):
    """Product stats for a period."""

    total_sales: int
    top_products: list[TopProductItem]
