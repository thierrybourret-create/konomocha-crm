from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.models import Contact, PipelineEntry, Order, ContactNote, PipelineNote, User
from app.auth import require_admin

router = APIRouter(prefix="/api/trash", tags=["trash"])

RETENTION_DAYS = 20


def _purge_expired(db: Session):
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    # Hard-delete items where deleted_at is older than retention period
    db.query(ContactNote).filter(
        ContactNote.deleted_at.isnot(None),
        ContactNote.deleted_at < cutoff
    ).delete(synchronize_session=False)
    db.query(PipelineNote).filter(
        PipelineNote.deleted_at.isnot(None),
        PipelineNote.deleted_at < cutoff
    ).delete(synchronize_session=False)
    db.query(Order).filter(
        Order.deleted_at.isnot(None),
        Order.deleted_at < cutoff
    ).delete(synchronize_session=False)
    db.query(PipelineEntry).filter(
        PipelineEntry.deleted_at.isnot(None),
        PipelineEntry.deleted_at < cutoff
    ).delete(synchronize_session=False)
    db.query(Contact).filter(
        Contact.deleted_at.isnot(None),
        Contact.deleted_at < cutoff
    ).delete(synchronize_session=False)
    db.commit()


def _days_since(dt):
    if dt is None:
        return 0
    delta = datetime.utcnow() - dt.replace(tzinfo=None) if dt.tzinfo else datetime.utcnow() - dt
    return max(0, delta.days)


def _days_remaining(dt):
    return max(0, RETENTION_DAYS - _days_since(dt))


@router.get("")
def get_trash(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    _purge_expired(db)

    contacts = db.query(Contact).filter(Contact.deleted_at.isnot(None)).all()
    pipeline = db.query(PipelineEntry).options(
        joinedload(PipelineEntry.contact),
        joinedload(PipelineEntry.brand),
    ).filter(PipelineEntry.deleted_at.isnot(None)).all()
    orders = db.query(Order).options(
        joinedload(Order.contact),
        joinedload(Order.brand),
    ).filter(Order.deleted_at.isnot(None)).all()
    contact_notes = db.query(ContactNote).options(
        joinedload(ContactNote.contact),
        joinedload(ContactNote.author),
    ).filter(ContactNote.deleted_at.isnot(None)).all()
    pipeline_notes = db.query(PipelineNote).options(
        joinedload(PipelineNote.pipeline_entry),
        joinedload(PipelineNote.author),
    ).filter(PipelineNote.deleted_at.isnot(None)).all()

    return {
        "contacts": [
            {
                "id": c.id,
                "name": c.name,
                "company": c.company,
                "email": c.email,
                "deleted_at": c.deleted_at.isoformat() if c.deleted_at else None,
                "days_since": _days_since(c.deleted_at),
                "days_remaining": _days_remaining(c.deleted_at),
            }
            for c in contacts
        ],
        "pipeline": [
            {
                "id": e.id,
                "contact_name": e.contact.name if e.contact else None,
                "brand_name": e.brand.name if e.brand else None,
                "status": e.status,
                "potential_value": float(e.potential_value) if e.potential_value else 0,
                "deleted_at": e.deleted_at.isoformat() if e.deleted_at else None,
                "days_since": _days_since(e.deleted_at),
                "days_remaining": _days_remaining(e.deleted_at),
            }
            for e in pipeline
        ],
        "orders": [
            {
                "id": o.id,
                "contact_name": o.contact.name if o.contact else None,
                "brand_name": o.brand.name if o.brand else None,
                "order_value": float(o.order_value) if o.order_value else 0,
                "status": o.status,
                "deleted_at": o.deleted_at.isoformat() if o.deleted_at else None,
                "days_since": _days_since(o.deleted_at),
                "days_remaining": _days_remaining(o.deleted_at),
            }
            for o in orders
        ],
        "contact_notes": [
            {
                "id": n.id,
                "contact_name": n.contact.name if n.contact else None,
                "body_preview": (n.body or "")[:100],
                "author_name": n.author.name if n.author else None,
                "deleted_at": n.deleted_at.isoformat() if n.deleted_at else None,
                "days_since": _days_since(n.deleted_at),
                "days_remaining": _days_remaining(n.deleted_at),
            }
            for n in contact_notes
        ],
        "pipeline_notes": [
            {
                "id": n.id,
                "pipeline_id": n.pipeline_id,
                "contact_name": n.pipeline_entry.contact.name if n.pipeline_entry and n.pipeline_entry.contact else None,
                "brand_name": n.pipeline_entry.brand.name if n.pipeline_entry and n.pipeline_entry.brand else None,
                "body_preview": (n.body or "")[:100],
                "author_name": n.author.name if n.author else None,
                "deleted_at": n.deleted_at.isoformat() if n.deleted_at else None,
                "days_since": _days_since(n.deleted_at),
                "days_remaining": _days_remaining(n.deleted_at),
            }
            for n in pipeline_notes
        ],
    }


VALID_TYPES = {"contact", "pipeline", "order", "contact_note", "pipeline_note"}


def _get_item(item_type: str, item_id: int, db: Session):
    if item_type == "contact":
        obj = db.query(Contact).filter(Contact.id == item_id, Contact.deleted_at.isnot(None)).first()
    elif item_type == "pipeline":
        obj = db.query(PipelineEntry).filter(PipelineEntry.id == item_id, PipelineEntry.deleted_at.isnot(None)).first()
    elif item_type == "order":
        obj = db.query(Order).filter(Order.id == item_id, Order.deleted_at.isnot(None)).first()
    elif item_type == "contact_note":
        obj = db.query(ContactNote).filter(ContactNote.id == item_id, ContactNote.deleted_at.isnot(None)).first()
    elif item_type == "pipeline_note":
        obj = db.query(PipelineNote).filter(PipelineNote.id == item_id, PipelineNote.deleted_at.isnot(None)).first()
    else:
        obj = None
    return obj


@router.post("/{item_type}/{item_id}/restore")
def restore_item(
    item_type: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if item_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid item_type. Must be one of: {sorted(VALID_TYPES)}")
    obj = _get_item(item_type, item_id, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found in trash")

    # For notes, verify parent still exists
    if item_type == "contact_note":
        note = obj
        parent = db.query(Contact).filter(Contact.id == note.contact_id).first()
        if not parent:
            raise HTTPException(status_code=409, detail="Parent contact no longer exists")
    elif item_type == "pipeline_note":
        note = obj
        parent = db.query(PipelineEntry).filter(PipelineEntry.id == note.pipeline_id).first()
        if not parent:
            raise HTTPException(status_code=409, detail="Parent pipeline entry no longer exists")

    obj.deleted_at = None
    db.commit()
    return {"ok": True}


@router.delete("/{item_type}/{item_id}")
def hard_delete_item(
    item_type: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if item_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid item_type. Must be one of: {sorted(VALID_TYPES)}")
    obj = _get_item(item_type, item_id, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found in trash")
    db.delete(obj)
    db.commit()
    return {"ok": True}
