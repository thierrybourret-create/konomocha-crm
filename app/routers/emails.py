from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.database import get_db
from app.models.models import EmailLog, User
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
