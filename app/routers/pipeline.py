from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, contains_eager
from sqlalchemy import or_, func
from typing import Optional
from datetime import date
from decimal import Decimal
from app.database import get_db
from app.models.models import PipelineEntry, Contact, Brand, User, PipelineStatus
from app.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

class PipelineCreate(BaseModel):
    contact_id: int
    brand_id: int
    status: PipelineStatus
    potential_value: Decimal
    next_action: Optional[str] = None
    due_date: Optional[date] = None
    owner_id: int
    notes: Optional[str] = None

def entry_to_dict(e: PipelineEntry):
    return {
        "id": e.id,
        "contact_id": e.contact_id,
        "contact_name": e.contact.name if e.contact else None,
        "contact_company": e.contact.company if e.contact else None,
        "brand_id": e.brand_id,
        "brand_name": e.brand.name if e.brand else None,
        "status": e.status,
        "potential_value": float(e.potential_value) if e.potential_value else None,
        "next_action": e.next_action,
        "due_date": e.due_date.isoformat() if e.due_date else None,
        "owner_id": e.owner_id,
        "owner_name": e.owner.name if e.owner else None,
        "notes": e.notes,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }

@router.get("")
def list_pipeline(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    brand_id: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("updated_at"),
    sort_dir: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = (
        db.query(PipelineEntry)
        .join(Contact, PipelineEntry.contact_id == Contact.id, isouter=True)
        .join(Brand, PipelineEntry.brand_id == Brand.id, isouter=True)
        .join(User, PipelineEntry.owner_id == User.id, isouter=True)
        .options(
            contains_eager(PipelineEntry.contact),
            contains_eager(PipelineEntry.brand),
            contains_eager(PipelineEntry.owner),
        )
    )
    if search:
        q = q.filter(or_(
            Contact.name.ilike(f"%{search}%"),
            Contact.company.ilike(f"%{search}%"),
            Brand.name.ilike(f"%{search}%"),
        ))
    if status:
        q = q.filter(PipelineEntry.status == status)
    if brand_id:
        q = q.filter(PipelineEntry.brand_id == brand_id)
    if owner_id:
        q = q.filter(PipelineEntry.owner_id == owner_id)

    sort_col = {
        "contact": Contact.company,
        "brand": Brand.name,
        "status": PipelineEntry.status,
        "due_date": PipelineEntry.due_date,
        "potential_value": PipelineEntry.potential_value,
    }.get(sort_by, PipelineEntry.updated_at)
    q = q.order_by(sort_col.desc() if sort_dir == "desc" else sort_col)

    total = q.count()
    total_value = db.query(func.sum(PipelineEntry.potential_value)).scalar() or 0
    entries = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "total_value": float(total_value),
        "page": page,
        "per_page": per_page,
        "results": [entry_to_dict(e) for e in entries],
    }

@router.get("/{entry_id}")
def get_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = (
        db.query(PipelineEntry)
        .join(Contact, PipelineEntry.contact_id == Contact.id, isouter=True)
        .join(Brand, PipelineEntry.brand_id == Brand.id, isouter=True)
        .join(User, PipelineEntry.owner_id == User.id, isouter=True)
        .options(
            contains_eager(PipelineEntry.contact),
            contains_eager(PipelineEntry.brand),
            contains_eager(PipelineEntry.owner),
        )
        .filter(PipelineEntry.id == entry_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry_to_dict(e)

@router.post("")
def create_entry(data: PipelineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "agent" and data.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Agents can only create entries assigned to themselves")
    e = PipelineEntry(**data.dict())
    db.add(e)
    db.commit()
    db.refresh(e)
    return entry_to_dict(e)

@router.put("/{entry_id}")
def update_entry(entry_id: int, data: PipelineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    if current_user.role == "agent" and e.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own entries")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return entry_to_dict(e)

@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    e = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(e)
    db.commit()
    return {"ok": True}
