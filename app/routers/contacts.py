import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
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
    owner_id: Optional[int] = None

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

    sort_col = {
        "name": Contact.name,
        "company": Contact.company,
        "country": Contact.country,
        "tags": Contact.tags,
        "region": Contact.tags,
        "last_name": func.split_part(Contact.name, ' ', 2),
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
                country=data.country, address=data.address, tags=data.tags, notes=data.notes,
                owner_id=data.owner_id, source="manual")
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
    for k in ("company", "email", "phone", "country", "address", "tags", "notes", "owner_id"):
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


class NoteCreate(BaseModel):
    body: str

@router.get("/{contact_id}/notes")
def get_contact_notes(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactNote
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    notes = db.query(ContactNote).filter(ContactNote.contact_id == contact_id).order_by(ContactNote.created_at.desc()).all()
    return [{"id": n.id, "body": n.body, "author_name": n.author.name, "created_at": n.created_at.isoformat()} for n in notes]

@router.post("/{contact_id}/notes")
def add_contact_note(contact_id: int, data: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactNote
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    note = ContactNote(contact_id=contact_id, body=data.body, author_id=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "body": note.body, "author_name": current_user.name, "created_at": note.created_at.isoformat()}


import uuid, shutil
from fastapi import UploadFile, File
from fastapi.responses import FileResponse

UPLOAD_DIR = "/home/thierry/konomocha-crm/uploads"

@router.post("/{contact_id}/attachments")
async def upload_attachment(
    contact_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models import ContactAttachment
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    dest_dir = os.path.join(UPLOAD_DIR, str(contact_id))
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored = str(uuid.uuid4()) + ext
    dest = os.path.join(dest_dir, stored)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(dest)
    att = ContactAttachment(contact_id=contact_id, filename=file.filename, stored_name=stored,
                            file_size=size, uploaded_by_id=current_user.id)
    db.add(att)
    db.commit()
    db.refresh(att)
    return {"id": att.id, "filename": att.filename, "file_size": att.file_size,
            "uploaded_by": current_user.name, "created_at": att.created_at.isoformat()}

@router.get("/{contact_id}/attachments")
def list_attachments(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactAttachment
    atts = db.query(ContactAttachment).filter(ContactAttachment.contact_id == contact_id).order_by(ContactAttachment.created_at.desc()).all()
    return [{"id": a.id, "filename": a.filename, "file_size": a.file_size,
             "uploaded_by": a.uploaded_by.name, "created_at": a.created_at.isoformat()} for a in atts]

@router.get("/{contact_id}/attachments/{att_id}/download")
def download_attachment(contact_id: int, att_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactAttachment
    att = db.query(ContactAttachment).filter(ContactAttachment.id == att_id, ContactAttachment.contact_id == contact_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    path = os.path.join(UPLOAD_DIR, str(contact_id), att.stored_name)
    return FileResponse(path, filename=att.filename)

@router.delete("/{contact_id}/attachments/{att_id}")
def delete_attachment(contact_id: int, att_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactAttachment
    att = db.query(ContactAttachment).filter(ContactAttachment.id == att_id, ContactAttachment.contact_id == contact_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    path = os.path.join(UPLOAD_DIR, str(contact_id), att.stored_name)
    if os.path.exists(path):
        os.remove(path)
    db.delete(att)
    db.commit()
    return {"ok": True}


class TaskCreate(BaseModel):
    title: str
    due_date: Optional[str] = None
    assigned_to_id: Optional[int] = None

@router.get("/{contact_id}/tasks")
def list_tasks(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactTask
    tasks = db.query(ContactTask).filter(ContactTask.contact_id == contact_id).order_by(ContactTask.completed, ContactTask.due_date).all()
    return [{"id": t.id, "title": t.title, "due_date": t.due_date.isoformat() if t.due_date else None,
             "completed": t.completed, "completed_at": t.completed_at.isoformat() if t.completed_at else None,
             "assigned_to": t.assigned_to.name if t.assigned_to else None,
             "created_by": t.created_by.name if t.created_by else None,
             "created_at": t.created_at.isoformat()} for t in tasks]

@router.post("/{contact_id}/tasks")
def create_task(contact_id: int, data: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactTask
    from datetime import date as _date
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    due = None
    if data.due_date:
        try: due = _date.fromisoformat(data.due_date)
        except: pass
    t = ContactTask(contact_id=contact_id, title=data.title, due_date=due,
                    assigned_to_id=data.assigned_to_id, created_by_id=current_user.id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "title": t.title, "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed": t.completed, "assigned_to": t.assigned_to.name if t.assigned_to else None,
            "created_by": current_user.name, "created_at": t.created_at.isoformat()}

@router.put("/{contact_id}/tasks/{task_id}")
def update_task(contact_id: int, task_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import ContactTask
    from datetime import datetime as _dt
    t = db.query(ContactTask).filter(ContactTask.id == task_id, ContactTask.contact_id == contact_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    if "completed" in data:
        t.completed = data["completed"]
        t.completed_at = _dt.utcnow() if data["completed"] else None
    db.commit()
    return {"ok": True}
