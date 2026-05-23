from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import date


class OrderCreate(BaseModel):
    contact_id: int
    brand_id: int
    order_date: date
    order_value: Decimal
    gross_commission_rate: Decimal = Decimal("0")
    testing_cost_deduction: Decimal = Decimal("0")
    owner_id: Optional[int] = None
    status: str = "po_received"
    notes: Optional[str] = None
    po_date: Optional[date] = None
    deposit_date: Optional[date] = None
    ship_date: Optional[date] = None
    fully_paid_date: Optional[date] = None
    commission_invoiced_date: Optional[date] = None
    commission_paid_date: Optional[date] = None
    bonus_paid_date: Optional[date] = None


class OrderStatusUpdate(BaseModel):
    status: str
    status_date: Optional[date] = None  # if None, use today


class BonusPaidRequest(BaseModel):
    order_ids: list
