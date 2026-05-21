### Patch models.py — remove OrderStatus enum, add date columns, change status to String ###
with open('/home/thierry/konomocha-crm/app/models/models.py', encoding='utf-8') as f:
    m = f.read()

# Remove OrderStatus enum
old_enum = (
    'class OrderStatus(str, enum.Enum):\n'
    '    confirmed = "Confirmed"\n'
    '    invoiced  = "Invoiced"\n'
    '    paid      = "Paid"\n'
    '\n'
)
if old_enum in m:
    m = m.replace(old_enum, '')
    print('OK: OrderStatus enum removed')
else:
    print('NOT FOUND: OrderStatus enum (may already be removed)')

# Update Order model body
old_cols = (
    '    gross_commission_rate  = Column(Numeric(5, 2), nullable=False)\n'
    '    testing_cost_deduction = Column(Numeric(12, 2), default=0)\n'
    '    net_commission         = Column(Numeric(12, 2))\n'
    '    status                 = Column(SAEnum(OrderStatus), default=OrderStatus.confirmed)\n'
    '    notes                  = Column(Text)\n'
)
new_cols = (
    '    po_date                = Column(Date)\n'
    '    pi_date                = Column(Date)\n'
    '    deposit_date           = Column(Date)\n'
    '    fob_date               = Column(Date)\n'
    '    payment_date           = Column(Date)\n'
    '    gross_commission_rate  = Column(Numeric(12, 2), default=0)\n'
    '    testing_cost_deduction = Column(Numeric(12, 2), default=0)\n'
    '    net_commission         = Column(Numeric(12, 2))\n'
    '    status                 = Column(String(100), default="PO Received")\n'
    '    notes                  = Column(Text)\n'
)
if old_cols in m:
    m = m.replace(old_cols, new_cols)
    print('OK: Order model columns updated')
else:
    print('NOT FOUND: Order model columns')

with open('/home/thierry/konomocha-crm/app/models/models.py', 'w', encoding='utf-8') as f:
    f.write(m)
print('models.py saved')

### Patch orders.py ###
ORDERS_PY = '''from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date
from decimal import Decimal
from app.database import get_db
from app.models.models import Order, User
from app.auth import get_current_user, require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/orders", tags=["orders"])

class OrderCreate(BaseModel):
    contact_id: int
    brand_id: int
    order_date: date
    order_value: Decimal
    currency: str = "USD"
    gross_commission_rate: Decimal = Decimal("0")
    testing_cost_deduction: Decimal = Decimal("0")
    po_date: Optional[date] = None
    pi_date: Optional[date] = None
    deposit_date: Optional[date] = None
    fob_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: str = "PO Received"
    notes: Optional[str] = None

def compute_net(commission_value, testing_cost):
    return (Decimal(str(commission_value)) - Decimal(str(testing_cost))).quantize(Decimal("0.01"))

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
        "commission_value": float(o.gross_commission_rate),
        "testing_cost_deduction": float(o.testing_cost_deduction),
        "net_commission": float(o.net_commission) if o.net_commission else None,
        "po_date": o.po_date.isoformat() if o.po_date else None,
        "pi_date": o.pi_date.isoformat() if o.pi_date else None,
        "deposit_date": o.deposit_date.isoformat() if o.deposit_date else None,
        "fob_date": o.fob_date.isoformat() if o.fob_date else None,
        "payment_date": o.payment_date.isoformat() if o.payment_date else None,
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
    net = compute_net(data.gross_commission_rate, data.testing_cost_deduction)
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
    o.net_commission = compute_net(o.gross_commission_rate, o.testing_cost_deduction)
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
'''

with open('/home/thierry/konomocha-crm/app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(ORDERS_PY)
print('orders.py saved')
