from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload, contains_eager
from app.database import get_db
from app.models.models import Contact, PipelineEntry, Order, Brand, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def global_search(
    q: str = Query("", min_length=1),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not q or not q.strip():
        return {"contacts": [], "pipeline": [], "orders": []}

    pat = f"%{q.strip()}%"

    # ── Contacts ──────────────────────────────────────────────────────────
    contacts_q = (
        db.query(Contact)
        .filter(
            Contact.deleted_at.is_(None),
            (
                Contact.name.ilike(pat)    |
                Contact.company.ilike(pat) |
                Contact.email.ilike(pat)   |
                Contact.phone.ilike(pat)
            ),
        )
        .order_by(Contact.name)
        .limit(limit)
        .all()
    )
    contacts = [
        {
            "id":      c.id,
            "name":    c.name,
            "company": c.company or "",
            "email":   c.email or "",
        }
        for c in contacts_q
    ]

    # ── Pipeline entries ──────────────────────────────────────────────────
    pipeline_q = (
        db.query(PipelineEntry)
        .join(Contact, PipelineEntry.contact_id == Contact.id)
        .join(Brand,   PipelineEntry.brand_id   == Brand.id)
        .options(
            contains_eager(PipelineEntry.contact),
            contains_eager(PipelineEntry.brand),
        )
        .filter(
            PipelineEntry.deleted_at.is_(None),
            (
                Contact.name.ilike(pat)  |
                Contact.company.ilike(pat) |
                Brand.name.ilike(pat)    |
                PipelineEntry.status.ilike(pat)
            ),
        )
        .order_by(PipelineEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    # #22: relationships already loaded via contains_eager — no per-row queries
    pipeline = [
        {
            "id":         e.id,
            "contact_id": e.contact_id,
            "contact":    e.contact.name if e.contact else "",
            "brand":      e.brand.name   if e.brand   else "",
            "status":     e.status or "",
            "value":      "{:,.2f}".format(float(e.potential_value)) if e.potential_value else "0.00",
        }
        for e in pipeline_q
    ]

    # ── Orders ────────────────────────────────────────────────────────────
    orders_q = (
        db.query(Order)
        .join(Contact, Order.contact_id == Contact.id)
        .join(Brand,   Order.brand_id   == Brand.id)
        .options(
            contains_eager(Order.contact),
            contains_eager(Order.brand),
        )
        .filter(
            Order.deleted_at.is_(None),
            (
                Contact.name.ilike(pat)    |
                Contact.company.ilike(pat) |
                Brand.name.ilike(pat)      |
                Order.status.ilike(pat)
            ),
        )
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    orders = [
        {
            "id":         o.id,
            "contact_id": o.contact_id,
            "contact":    o.contact.name if o.contact else "",
            "brand":      o.brand.name   if o.brand   else "",
            "status":     o.status or "",
            "value":      "{:,.2f}".format(float(o.order_value)) if o.order_value else "0.00",
        }
        for o in orders_q
    ]

    return {"contacts": contacts, "pipeline": pipeline, "orders": orders}
