#!/usr/bin/env python3
"""
Rewrites contacts router with source filter, sorting, and first/last name split.
Run from: /home/thierry/konomocha-crm (with venv active)
"""
import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')

target = '/home/thierry/konomocha-crm/app/routers/contacts.py'

new_content = '''from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.database import get_db
from app.models.models import Contact, User
from app.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

class ContactCreate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None

class ContactUpdate(ContactCreate):
    pass

def contact_to_dict(c):
    parts = (c.name or "").split(" ", 1)
    return {
        "id": c.id,
        "name": c.name,
        "first_name": parts[0] if parts else "",
        "last_name": parts[1] if len(parts) > 1 else "",
        "company": c.company,
        "email": c.email,
        "phone": c.phone,
        "country": c.country,
        "address": c.address,
        "tags": c.tags,
        "notes": c.notes,
        "source": c.source,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

@router.get("")
def list_contacts(
    search: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("name"),
    sort_dir: Optional[str] = Query("asc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Contact)

    # Source filter — key fix for contacts vs companies split
    if source == "contacts":
        q = q.filter(Contact.source.in_(["lacrm_import", "manual"]))
    elif source == "companies":
        q = q.filter(Contact.source.in_(["lacrm_company_import"]))
    elif source:
        q = q.filter(Contact.source == source)

    if search:
        q = q.filter(or_(
            Contact.name.ilike(f"%{search}%"),
            Contact.company.ilike(f"%{search}%"),
            Contact.email.ilike(f"%{search}%"),
        ))
    if country:
        q = q.filter(Contact.country == country)

    # Sorting
    sort_col = {
        "name": Contact.name,
        "company": Contact.company,
        "country": Contact.country,
    }.get(sort_by, Contact.name)
    if sort_dir == "desc":
        sort_col = sort_col.desc()
    q = q.order_by(sort_col)

    total = q.count()
    results = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "results": [contact_to_dict(c) for c in results]
    }

@router.get("/{contact_id}")
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Contact).filter(Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    return contact_to_dict(c)

@router.post("")
def create_contact(data: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    name = ((data.first_name or "") + " " + (data.last_name or "")).strip() or data.name or "Unknown"
    c = Contact(name=name, company=data.company, email=data.email, phone=data.phone,
                country=data.country, address=data.address, tags=data.tags, notes=data.notes, source="manual")
    db.add(c)
    db.commit()
    db.refresh(c)
    return contact_to_dict(c)

@router.put("/{contact_id}")
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Contact).filter(Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    if data.first_name is not None or data.last_name is not None:
        c.name = ((data.first_name or "") + " " + (data.last_name or "")).strip() or c.name
    elif data.name:
        c.name = data.name
    for k in ("company", "email", "phone", "country", "address", "tags", "notes"):
        v = getattr(data, k)
        if v is not None:
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return contact_to_dict(c)

@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    c = db.query(Contact).filter(Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(c)
    db.commit()
    return {"ok": True}
'''

with open(target, 'w') as f:
    f.write(new_content)
print("contacts.py rewritten.")
