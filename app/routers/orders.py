from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from decimal import Decimal
from app.database import get_db
from app.models.models import Order, User, Contact
from app.auth import get_current_user, require_admin
from app.constants import (ORDER_STATUSES, ORDER_STATUS_LABELS, ORDER_STATUS_DATES,
                            BONUS_RATE, COMMISSION_LAG_DAYS)
from app.schemas.orders import OrderCreate, OrderStatusUpdate, BonusPaidRequest
from app.permissions import has_scope_all
from app.audit import log_audit, diff_and_log, log_created_order, fmt_num, ORDER_TRACKED

router = APIRouter(prefix="/api/orders", tags=["orders"])



def compute_net(order_value, rate, deduction):
    v = Decimal(str(order_value))
    r = Decimal(str(rate))
    d = Decimal(str(deduction))
    return ((v * r / 100) - d).quantize(Decimal("0.01"))


def compute_bonus(net_commission, owner):
    if owner and getattr(owner, "role", None) == "agent":
        return (Decimal(str(net_commission)) * BONUS_RATE).quantize(Decimal("0.01"))
    return None


def commission_due(ship_date):
    if ship_date:
        return ship_date + timedelta(days=COMMISSION_LAG_DAYS)
    return None


def order_to_dict(o: Order):
    cdd = commission_due(o.ship_date)
    idx = ORDER_STATUSES.index(o.status) if o.status in ORDER_STATUSES else -1
    next_status = ORDER_STATUSES[idx + 1] if idx >= 0 and idx < len(ORDER_STATUSES) - 1 else None
    return {
        "id":                       o.id,
        "contact_id":               o.contact_id,
        "contact_name":             o.contact.name    if o.contact else None,
        "contact_company":          o.contact.company if o.contact else None,
        "brand_id":                 o.brand_id,
        "brand_name":               o.brand.name      if o.brand   else None,
        "order_date":               o.order_date.isoformat() if o.order_date else None,
        "order_value":              float(o.order_value),
        "gross_commission_rate":    float(o.gross_commission_rate),
        "testing_cost_deduction":   float(o.testing_cost_deduction),
        "net_commission":           float(o.net_commission) if o.net_commission is not None else None,
        "bonus_amount":             float(o.bonus_amount) if o.bonus_amount is not None else None,
        "owner_id":                 o.owner_id,
        "owner_name":               o.owner.name if o.owner else None,
        "status":                   o.status,
        "status_label":             ORDER_STATUS_LABELS.get(o.status, o.status),
        "status_index":             idx,
        "next_status":              next_status,
        "next_status_label":        ORDER_STATUS_LABELS.get(next_status) if next_status else None,
        "po_date":                  o.po_date.isoformat()                   if o.po_date                   else None,
        "deposit_date":             o.deposit_date.isoformat()              if o.deposit_date               else None,
        "ship_date":                o.ship_date.isoformat()                 if o.ship_date                  else None,
        "fully_paid_date":          o.fully_paid_date.isoformat()           if o.fully_paid_date            else None,
        "commission_invoiced_date": o.commission_invoiced_date.isoformat()  if o.commission_invoiced_date   else None,
        "commission_paid_date":     o.commission_paid_date.isoformat()      if o.commission_paid_date       else None,
        "bonus_paid_date":          o.bonus_paid_date.isoformat()           if o.bonus_paid_date            else None,
        "commission_due_date":      cdd.isoformat() if cdd else None,
        "notes":                    o.notes,
        "created_at":               o.created_at.isoformat() if o.created_at else None,
    }


def _base_query(db):
    return db.query(Order).options(
        joinedload(Order.contact),
        joinedload(Order.brand),
        joinedload(Order.owner),
    )


@router.get("")
def list_orders(
    status: Optional[str]   = Query(None),
    owner_id: Optional[int]  = Query(None),
    brand_id: Optional[int]  = Query(None),
    date_from: Optional[date] = Query(None),
    date_to:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = _base_query(db).filter(Order.deleted_at.is_(None))
    if not has_scope_all(current_user, "orders"):
        q = q.filter(Order.owner_id == current_user.id)
    elif owner_id:
        q = q.filter(Order.owner_id == owner_id)
    if status:
        q = q.filter(Order.status == status)
    if brand_id:
        q = q.filter(Order.brand_id == brand_id)
    if date_from:
        q = q.filter(Order.ship_date >= date_from)
    if date_to:
        q = q.filter(Order.ship_date <= date_to)
    total = q.count()
    orders = q.order_by(Order.order_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "results": [order_to_dict(o) for o in orders]}


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = _base_query(db).filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != "admin" and o.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    return order_to_dict(o)


@router.post("")
def create_order(data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    d = data.dict()
    if not d.get("owner_id"):
        d["owner_id"] = current_user.id
    net = compute_net(d["order_value"], d["gross_commission_rate"], d["testing_cost_deduction"])
    owner = db.query(User).filter(User.id == d["owner_id"]).first() if d.get("owner_id") else None
    bonus = compute_bonus(net, owner)
    o = Order(**d, net_commission=net, bonus_amount=bonus)
    db.add(o)
    db.commit()
    db.refresh(o)
    db.refresh(o, attribute_names=["contact", "brand", "owner"])
    log_created_order(db, o, current_user.id, current_user.name)
    db.commit()
    return order_to_dict(o)


@router.put("/mark-bonus-paid")
def mark_bonus_paid(
    data: BonusPaidRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    today = date.today()
    updated = 0
    for oid in data.order_ids:
        o = db.query(Order).filter(Order.id == oid, Order.status == 'commission_paid', Order.deleted_at.is_(None)).first()
        if o:
            o.status = 'bonus_paid'
            o.bonus_paid_date = today
            updated += 1
    db.commit()
    return {"updated": updated}


@router.put("/{order_id}")
def update_order(order_id: int, data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = _base_query(db).filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != "admin" and o.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    _update = data.dict(exclude_unset=True)
    # Only admins may reassign owner, brand, or contact on an existing order
    if current_user.role != "admin":
        for _restricted in ("owner_id", "brand_id", "contact_id"):
            _update.pop(_restricted, None)
    _snap  = {f: getattr(o, f, None) for f in ORDER_TRACKED}
    _cname = o.contact.name if o.contact else None
    _bname = o.brand.name   if o.brand   else None
    for k, v in _update.items():
        setattr(o, k, v)
    o.net_commission = compute_net(o.order_value, o.gross_commission_rate, o.testing_cost_deduction)
    owner = db.query(User).filter(User.id == o.owner_id).first() if o.owner_id else None
    o.bonus_amount = compute_bonus(o.net_commission, owner)
    db.commit()
    db.refresh(o)
    diff_and_log(db, entity_type='order', entity_id=order_id,
                 contact_name=_cname, brand_name=_bname,
                 old_obj=type('S', (), _snap)(), new_data=_update,
                 tracked_fields=ORDER_TRACKED,
                 resolve={'order_value': fmt_num, 'gross_commission_rate': fmt_num, 'testing_cost_deduction': fmt_num},
                 user_id=current_user.id, user_name=current_user.name)
    db.commit()
    return order_to_dict(o)


@router.post("/{order_id}/advance-status")
def advance_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = _base_query(db).filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != "admin" and o.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    if data.status == "bonus_paid" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only for bonus_paid")
    if data.status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {ORDER_STATUSES}")
    _old_status = o.status
    _cname = o.contact.name if o.contact else None
    _bname = o.brand.name   if o.brand   else None
    o.status = data.status
    date_field = ORDER_STATUS_DATES.get(data.status)
    if date_field:
        setattr(o, date_field, data.status_date or date.today())
    if data.status == "bonus_paid":
        o.bonus_paid_date = data.status_date or date.today()
    db.commit()
    db.refresh(o)
    log_audit(db, entity_type='order', entity_id=order_id,
              contact_name=_cname, brand_name=_bname,
              action='updated', field_name='status',
              old_value=_old_status, new_value=data.status,
              user_id=current_user.id, user_name=current_user.name)
    db.commit()
    return order_to_dict(o)


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    o = db.query(Order).filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    _cname = o.contact.name if o.contact else None
    _bname = o.brand.name   if o.brand   else None
    o.deleted_at = datetime.now(timezone.utc)
    log_audit(db, entity_type='order', entity_id=order_id,
              contact_name=_cname, brand_name=_bname,
              action='deleted', user_id=current_user.id, user_name=current_user.name)
    db.commit()
    return {"ok": True}


