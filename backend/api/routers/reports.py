"""Report endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from backend.api.deps import CurrentUser, require_permission
from backend.api.schemas.reports import (
    CustomerSummaryResponse,
    DailySalesItem,
    ProductSummaryResponse,
    SalesSummaryResponse,
)
from backend.repositories.sales_repository import get_daily_sales
from backend.services.report_service import (
    get_customer_summary,
    get_product_summary,
    get_sales_summary,
)


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales-summary", response_model=SalesSummaryResponse)
def sales_summary(
    start_date: date = Query(),
    end_date: date = Query(),
    current_user: CurrentUser = Depends(require_permission("export")),
):
    """Returns a sales summary for a period."""
    return get_sales_summary(
        str(start_date),
        str(end_date),
        lavanderia_id=current_user.lavanderia_id,
    )


@router.get("/daily-sales", response_model=list[DailySalesItem])
def daily_sales(
    start_date: date = Query(),
    end_date: date = Query(),
    current_user: CurrentUser = Depends(require_permission("export")),
):
    """Returns total sales grouped by day for trend charts."""
    rows = get_daily_sales(
        str(start_date),
        str(end_date),
        lavanderia_id=current_user.lavanderia_id,
    )
    return [{"date": str(row["date"]), "total": float(row["total"])} for row in rows]


@router.get("/customer-summary", response_model=CustomerSummaryResponse)
def customer_summary(
    start_date: date = Query(),
    end_date: date = Query(),
    current_user: CurrentUser = Depends(require_permission("export")),
):
    """Returns customer/vehicle stats for a period."""
    return get_customer_summary(
        str(start_date),
        str(end_date),
        lavanderia_id=current_user.lavanderia_id,
    )


@router.get("/product-summary", response_model=ProductSummaryResponse)
def product_summary(
    start_date: date = Query(),
    end_date: date = Query(),
    current_user: CurrentUser = Depends(require_permission("export")),
):
    """Returns product stats for a period."""
    return get_product_summary(
        str(start_date),
        str(end_date),
        lavanderia_id=current_user.lavanderia_id,
    )
