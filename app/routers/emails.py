from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.database import get_db
from app.models.models import EmailLog, User, Contact
from app.auth import get_current_user

router = APIRouter(prefix="/api/emails", tags=["emails"])

def email_to_dict(e: EmailLog):
    return {
        "id": e.id,
        "contact_id": e.contact_id,
        "contact_name": e.contact.name if e.contact else None,
        "contact_company": e.contact.company if e.contact else None,
        "direction": e.direction,
        "sent_at": e.sent_at.isoformat() if e.sent_at else None,
        "subject": e.subject,
        "body_snippet": e.body_snippet,
        "from_address": e.from_address,
        "to_address": e.to_address,
    }

@router.get("")
def list_emails(
    contact_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(EmailLog).options(joinedload(EmailLog.contact))
    if contact_id:
        q = q.filter(EmailLog.contact_id == contact_id)
    total = q.count()
    emails = q.order_by(EmailLog.sent_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "results": [email_to_dict(e) for e in emails]}

from typing import Optional as _Opt
from pydantic import BaseModel as _BM
from datetime import datetime as _dt

class EmailCreate(_BM):
    direction: str
    from_address: _Opt[str] = None
    to_address:   _Opt[str] = None
    subject:      _Opt[str] = None
    body_snippet: _Opt[str] = None
    sent_at:      _Opt[str] = None
    raw_message_id: _Opt[str] = None

@router.post("")
def log_email(data: EmailCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.direction not in ("inbound", "outbound"):
        raise HTTPException(status_code=422, detail="direction must be inbound or outbound")
    match_addr = data.from_address if data.direction == "inbound" else data.to_address
    contact = None
    if match_addr:
        contact = db.query(Contact).filter(Contact.email == match_addr).first()
        if not contact:
            # Auto-create incomplete contact — will appear in quality report
            raw = match_addr.split("@")[0].replace(".", " ").replace("_", " ").title()
            contact = Contact(name=raw or match_addr, email=match_addr, source="email_auto")
            db.add(contact)
            db.flush()
    sent = _dt.utcnow()
    if data.sent_at:
        try: sent = _dt.fromisoformat(data.sent_at.replace("Z", "+00:00"))
        except: pass
    log = EmailLog(
        contact_id=contact.id if contact else None,
        direction=data.direction,
        from_address=data.from_address,
        to_address=data.to_address,
        subject=data.subject,
        body_snippet=data.body_snippet,
        sent_at=sent,
        raw_message_id=data.raw_message_id,
        logged_by_id=current_user.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {**email_to_dict(log), "contact_created": contact is not None and contact.source == "email_auto"}
