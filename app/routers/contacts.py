import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from app.database import get_db
from app.models.models import Contact, User, ContactNote
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
    job_title: Optional[str] = None
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
        "job_title": c.job_title or "",
        "country": c.country,
        "address": c.address,
        "tags": c.tags,
        "notes": c.notes,
        "source": c.source,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

@router.get("/duplicates")
def list_all_duplicates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all pairs of contacts that share the same non-empty email."""
    from sqlalchemy import func as sqlfunc
    from app.models.models import Contact as C2
    # find emails shared by 2+ contacts
    dupes = (
        db.query(Contact.email, sqlfunc.count(Contact.id).label("cnt"))
        .filter(Contact.email.isnot(None), Contact.email != "",
                Contact.deleted_at.is_(None))
        .group_by(Contact.email)
        .having(sqlfunc.count(Contact.id) > 1)
        .all()
    )
    pairs = []
    for row in dupes:
        contacts = (
            db.query(Contact)
            .filter(Contact.email == row.email, Contact.deleted_at.is_(None))
            .order_by(Contact.id)
            .all()
        )
        for i in range(len(contacts)):
            for j in range(i + 1, len(contacts)):
                a, b = contacts[i], contacts[j]
                pairs.append({
                    "email":    row.email,
                    "contact_a": {"id": a.id, "name": a.name, "company": a.company},
                    "contact_b": {"id": b.id, "name": b.name, "company": b.company},
                })
    return {"total": len(pairs), "pairs": pairs}


@router.get("/{contact_id}/duplicates")
def find_contact_duplicates(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return contacts that share the same email as the given contact."""
    contact = db.query(Contact).filter(
        Contact.id == contact_id, Contact.deleted_at.is_(None)
    ).first()
    if not contact or not contact.email:
        return {"duplicates": []}
    matches = (
        db.query(Contact)
        .filter(
            Contact.email == contact.email,
            Contact.id != contact_id,
            Contact.deleted_at.is_(None),
        )
        .all()
    )
    return {
        "duplicates": [
            {"id": c.id, "name": c.name, "company": c.company or "", "email": c.email}
            for c in matches
        ]
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
    q = db.query(Contact).filter(Contact.deleted_at.is_(None))

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
    c = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    return contact_to_dict(c)

@router.post("")
def create_contact(data: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    name = ((data.first_name or "") + " " + (data.last_name or "")).strip() or data.name or "Unknown"
    c = Contact(name=name, company=data.company, email=data.email, phone=data.phone,
                job_title=data.job_title, country=data.country, address=data.address, tags=data.tags, notes=data.notes,
                owner_id=data.owner_id, source="manual")
    db.add(c)
    db.commit()
    db.refresh(c)
    return contact_to_dict(c)

@router.put("/{contact_id}")
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    if data.first_name is not None or data.last_name is not None:
        c.name = ((data.first_name or "") + " " + (data.last_name or "")).strip() or c.name
    elif data.name:
        c.name = data.name
    for k in ("company", "email", "phone", "job_title", "country", "address", "tags", "notes", "owner_id"):
        v = getattr(data, k)
        if v is not None:
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return contact_to_dict(c)

@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    c.deleted_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


class NoteCreate(BaseModel):
    body: str

@router.get("/{contact_id}/notes")
def get_contact_notes(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    notes = db.query(ContactNote).filter(
        ContactNote.contact_id == contact_id,
        ContactNote.deleted_at.is_(None)
    ).order_by(ContactNote.created_at.desc()).all()
    return [{"id": n.id, "body": n.body, "author_name": n.author.name, "created_at": n.created_at.isoformat()} for n in notes]

@router.post("/{contact_id}/notes")
def add_contact_note(contact_id: int, data: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    note = ContactNote(contact_id=contact_id, body=data.body, author_id=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "body": note.body, "author_name": current_user.name, "created_at": note.created_at.isoformat()}

@router.delete("/{contact_id}/notes/{note_id}")
def delete_contact_note(contact_id: int, note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(ContactNote).filter(
        ContactNote.id == note_id,
        ContactNote.contact_id == contact_id,
        ContactNote.deleted_at.is_(None)
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != "admin" and note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    note.deleted_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


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
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
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
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
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


class MergeRequest(BaseModel):
    duplicate_id: int

@router.get("/{master_id}/merge-preview/{dup_id}")
def merge_preview(
    master_id: int, dup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if master_id == dup_id:
        raise HTTPException(status_code=400, detail="Cannot merge a contact with itself")
    from app.models.models import PipelineEntry, EmailLog, Order, ContactAttachment, ContactTask
    master = db.query(Contact).filter(Contact.id == master_id, Contact.deleted_at.is_(None)).first()
    dup    = db.query(Contact).filter(Contact.id == dup_id, Contact.deleted_at.is_(None)).first()
    if not master or not dup:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {
        "master_name": master.name,
        "dup_name":    dup.name,
        "pipeline":    db.query(PipelineEntry).filter(PipelineEntry.contact_id == dup_id).count(),
        "emails":      db.query(EmailLog).filter(EmailLog.contact_id == dup_id).count(),
        "orders":      db.query(Order).filter(Order.contact_id == dup_id).count(),
        "notes":       db.query(ContactNote).filter(ContactNote.contact_id == dup_id).count(),
        "tasks":       db.query(ContactTask).filter(ContactTask.contact_id == dup_id).count(),
        "attachments": db.query(ContactAttachment).filter(ContactAttachment.contact_id == dup_id).count(),
    }

@router.post("/{master_id}/merge")
def merge_contacts(
    master_id: int, data: MergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dup_id = data.duplicate_id
    if master_id == dup_id:
        raise HTTPException(status_code=400, detail="Cannot merge a contact with itself")
    from app.models.models import PipelineEntry, EmailLog, Order, ContactAttachment, ContactTask
    master = db.query(Contact).filter(Contact.id == master_id, Contact.deleted_at.is_(None)).first()
    dup    = db.query(Contact).filter(Contact.id == dup_id, Contact.deleted_at.is_(None)).first()
    if not master or not dup:
        raise HTTPException(status_code=404, detail="Contact not found")

    import shutil, os as _os

    # Move all FK-linked records to master
    db.query(PipelineEntry).filter(PipelineEntry.contact_id == dup_id).update({"contact_id": master_id})
    db.query(EmailLog).filter(EmailLog.contact_id == dup_id).update({"contact_id": master_id})
    db.query(Order).filter(Order.contact_id == dup_id).update({"contact_id": master_id})
    db.query(ContactNote).filter(ContactNote.contact_id == dup_id).update({"contact_id": master_id})
    db.query(ContactTask).filter(ContactTask.contact_id == dup_id).update({"contact_id": master_id})

    # Attachments: update DB rows first, then move files AFTER commit
    UPLOAD_DIR = "/home/thierry/konomocha-crm/uploads"
    atts = db.query(ContactAttachment).filter(ContactAttachment.contact_id == dup_id).all()
    att_names = [att.stored_name for att in atts]
    if atts:
        db.query(ContactAttachment).filter(ContactAttachment.contact_id == dup_id).update({"contact_id": master_id})

    db.delete(dup)
    db.commit()  # commit all DB changes before touching the filesystem

    # Move files on disk after successful commit
    if att_names:
        master_dir = _os.path.join(UPLOAD_DIR, str(master_id))
        dup_dir    = _os.path.join(UPLOAD_DIR, str(dup_id))
        _os.makedirs(master_dir, exist_ok=True)
        for stored_name in att_names:
            src = _os.path.join(dup_dir, stored_name)
            dst = _os.path.join(master_dir, stored_name)
            try:
                if _os.path.exists(src):
                    shutil.move(src, dst)
            except Exception as exc:
                from app.logger import app_logger
                app_logger.error("merge_contacts: failed to move " + src + " -> " + dst + ": " + str(exc))

    # Try to remove the now-empty dup upload dir
    dup_dir = _os.path.join(UPLOAD_DIR, str(dup_id))
    if _os.path.exists(dup_dir):
        try: _os.rmdir(dup_dir)
        except: pass
    db.refresh(master)
    return {"ok": True, "master": contact_to_dict(master)}

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
