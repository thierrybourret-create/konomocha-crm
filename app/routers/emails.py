import os
import secrets as _secrets
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
        "bcc_address": e.bcc_address,
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
    if str(current_user.role) != 'admin':
        q = q.filter(EmailLog.logged_by_id == current_user.id)
    total = q.count()
    emails = q.order_by(EmailLog.sent_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "results": [email_to_dict(e) for e in emails]}

from datetime import datetime as _dt
from app.schemas.emails import EmailCreate

@router.post("")
def log_email(data: EmailCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.direction not in ("inbound", "outbound"):
        raise HTTPException(status_code=422, detail="direction must be inbound or outbound")
    match_addr = data.from_address if data.direction == "inbound" else data.to_address
    contact = None
    if match_addr:
        # #42: lock the row to serialise concurrent inbound emails from the same address
        contact = db.query(Contact).filter(Contact.email == match_addr).with_for_update().first()
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
        bcc_address=data.bcc_address,
        logged_by_id=current_user.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {**email_to_dict(log), "contact_created": contact is not None and contact.source == "email_auto"}


_INBOUND_TOKEN = os.getenv("INBOUND_TOKEN")
if not _INBOUND_TOKEN:
    raise RuntimeError("INBOUND_TOKEN environment variable is required")

from fastapi import Request as _Request

@router.post("/inbound")
async def receive_inbound_email(request: _Request, db: Session = Depends(get_db)):
    """Called by the Postfix pipe script when a BCC email arrives."""
    token = request.headers.get('X-Inbound-Token', '')
    if not _secrets.compare_digest(token, _INBOUND_TOKEN):
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    direction = data.get('direction', 'outbound')
    if direction not in ('inbound', 'outbound'):
        direction = 'outbound'

    from_address = data.get('from_address')
    to_address   = data.get('to_address')

    # Auto-match or auto-create contact from the customer address
    # For outbound BCC: customer is the To address
    match_addr = to_address if direction == 'outbound' else from_address
    contact = None
    if match_addr:
        contact = db.query(Contact).filter(Contact.email == match_addr).first()
        if not contact:
            raw_name = match_addr.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            contact = Contact(name=raw_name or match_addr, email=match_addr, source='email_auto')
            db.add(contact)
            db.flush()

    sent = _dt.utcnow()
    sent_raw = data.get('sent_at')
    if sent_raw:
        try:
            sent = _dt.fromisoformat(sent_raw.replace('Z', '+00:00'))
        except Exception:
            pass

    log = EmailLog(
        contact_id=contact.id if contact else None,
        direction=direction,
        from_address=from_address,
        to_address=to_address,
        subject=data.get('subject'),
        body_snippet=data.get('body_snippet'),
        sent_at=sent,
        logged_by_id=None,
    )
    db.add(log)
    db.commit()
    return {"ok": True, "contact_id": contact.id if contact else None}

