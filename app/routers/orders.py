from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date
from decimal import Decimal
from app.database import get_db
from app.models.models import Order, User, OrderStatus
from app.auth import get_current_user, require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/orders", tags=["orders"])

class OrderCreate(BaseModel):
    contact_id: int
    brand_id: int
    order_date: date
    order_value: Decimal
    currency: str = "USD"
    gross_commission_rate: Decimal
    testing_cost_deduction: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.confirmed
    notes: Optional[str] = None

def compute_net(order_value, gross_rate, testing_cost):
    gross = (order_value * gross_rate / 100).quantize(Decimal("0.01"))
    return (gross - testing_cost).quantize(Decimal("0.01"))

def order_to_dict(o: Order):
    return {
        "id": o.id,
        "contact_id": o.contact_id,
        "contact_name": o.contact.name if o.contact else None,
        "contact_company": o.contact.company if o.contact else None,
        "brand_id": o.brand_id,
        "brand_name": o.brand.name if o.brand else None,
        "order_date": o.order_date.isoformat() if o.order_date else None,
        "order_value": float(o.order_value),
        "currency": o.currency,
        "gross_commission_rate": float(o.gross_commission_rate),
        "testing_cost_deduction": float(o.testing_cost_deduction),
        "net_commission": float(o.net_commission) if o.net_commission else None,
        "status": o.status,
        "notes": o.notes,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }

@router.get("")
def list_orders(
    brand_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    q = db.query(Order).options(joinedload(Order.contact), joinedload(Order.brand))
    if brand_id:
        q = q.filter(Order.brand_id == brand_id)
    if status:
        q = q.filter(Order.status == status)
    total = q.count()
    orders = q.order_by(Order.order_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "results": [order_to_dict(o) for o in orders]}

@router.post("")
def create_order(data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    net = compute_net(data.order_value, data.gross_commission_rate, data.testing_cost_deduction)
    o = Order(**data.dict(), net_commission=net)
    db.add(o)
    db.commit()
    db.refresh(o)
    return order_to_dict(o)

@router.put("/{order_id}")
def update_order(order_id: int, data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(o, k, v)
    o.net_commission = compute_net(o.order_value, o.gross_commission_rate, o.testing_cost_deduction)
    db.commit()
    db.refresh(o)
    return order_to_dict(o)

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(o)
    db.commit()
    return {"ok": True}
