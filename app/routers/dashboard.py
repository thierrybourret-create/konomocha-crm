from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.database import get_db
from app.models.models import PipelineEntry, Order, EmailLog, User, PipelineStatus
from app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

ACTIVE_STATUSES = [
    PipelineStatus.awaiting_feedback, PipelineStatus.awaiting_info,
    PipelineStatus.awaiting_samples, PipelineStatus.catalogue_sent,
    PipelineStatus.deposit_paid, PipelineStatus.form_completed,
    PipelineStatus.in_progress, PipelineStatus.order_placed,
    PipelineStatus.price_list_sent, PipelineStatus.pricing_sent,
    PipelineStatus.quotation_sent, PipelineStatus.samples_delivered,
    PipelineStatus.samples_requested, PipelineStatus.samples_sent,
]

@router.get("")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_active = db.query(PipelineEntry).filter(PipelineEntry.status.in_(ACTIVE_STATUSES)).count()
    overdue = db.query(PipelineEntry).filter(
        PipelineEntry.due_date < date.today(),
        PipelineEntry.status.in_(ACTIVE_STATUSES)
    ).count()
    total_pipeline_value = db.query(func.sum(PipelineEntry.potential_value)).filter(
        PipelineEntry.status.in_(ACTIVE_STATUSES)
    ).scalar() or 0
    commission_due = db.query(func.sum(Order.net_commission)).filter(
        Order.status != "paid"
    ).scalar() or 0
    recent_emails = db.query(EmailLog).order_by(EmailLog.sent_at.desc()).limit(5).all()
    return {
        "total_active_pipeline": total_active,
        "overdue_actions": overdue,
        "total_pipeline_value": float(total_pipeline_value),
        "commission_due": float(commission_due),
        "recent_emails": [
            {"id": e.id, "subject": e.subject, "direction": e.direction,
             "sent_at": e.sent_at.isoformat() if e.sent_at else None}
            for e in recent_emails
        ]
    }
