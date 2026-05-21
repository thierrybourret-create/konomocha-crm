from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.database import get_db
from app.models.models import PipelineEntry, Order, EmailLog, User, ContactTask, Contact
from app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

ACTIVE_STATUSES = [
    'Awaiting Feedback', 'Awaiting Info', 'Awaiting Samples',
    'Catalogue Sent', 'Deposit Paid', 'Form Completed', 'In Progress',
    'Order Placed', 'Price List Sent', 'Quotation Sent',
    'Samples Delivered', 'Samples Requested', 'Samples Sent',
]

@router.get("")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today    = date.today()
    is_admin = getattr(current_user, "role", None) == "admin"
    uid      = current_user.id

    # ── Pipeline KPIs (filtered for non-admin) ───────────────────────────────
    pq = db.query(PipelineEntry).filter(PipelineEntry.status.in_(ACTIVE_STATUSES))
    if not is_admin:
        pq = pq.filter(PipelineEntry.owner_id == uid)

    total_active     = pq.count()
    overdue_pipeline = pq.filter(PipelineEntry.due_date < today).count()

    val_q = db.query(func.sum(PipelineEntry.potential_value)).filter(PipelineEntry.status.in_(ACTIVE_STATUSES))
    if not is_admin:
        val_q = val_q.filter(PipelineEntry.owner_id == uid)
    total_pipeline_value = val_q.scalar() or 0

    # ── Commission due (via order owner) ─────────────────────────────────────
    comm_q = db.query(func.sum(Order.net_commission)).filter(Order.status != "paid")
    if not is_admin:
        comm_q = comm_q.filter(Order.owner_id == uid)
    commission_due = comm_q.scalar() or 0

    # ── Recent emails ─────────────────────────────────────────────────────────
    eq = db.query(EmailLog).order_by(EmailLog.sent_at.desc())
    if not is_admin:
        eq = eq.filter(EmailLog.logged_by_id == uid)
    recent_emails = eq.limit(6).all()

    # ── Pipeline by stage ─────────────────────────────────────────────────────
    sq = (db.query(PipelineEntry.status,
                   func.count(PipelineEntry.id).label("cnt"),
                   func.sum(PipelineEntry.potential_value).label("val"))
          .filter(PipelineEntry.status.in_(ACTIVE_STATUSES)))
    if not is_admin:
        sq = sq.filter(PipelineEntry.owner_id == uid)
    stage_rows = sq.group_by(PipelineEntry.status).order_by(func.count(PipelineEntry.id).desc()).all()

    # ── Today's actions (tasks) ───────────────────────────────────────────────
    tq = (db.query(ContactTask, Contact.name.label("cname"), Contact.company.label("ccompany"))
          .join(Contact, ContactTask.contact_id == Contact.id)
          .filter(ContactTask.completed == False, ContactTask.due_date <= today))
    if not is_admin:
        tq = tq.filter(ContactTask.assigned_to_id == uid)
    today_tasks = tq.order_by(ContactTask.due_date).limit(10).all()

    # ── Team workload (admin only shows all users; others show just themselves) ─
    if is_admin:
        wl_users = db.query(User).filter(User.is_active == True).all()
        tt_rows = (db.query(ContactTask.assigned_to_id, func.count(ContactTask.id).label("cnt"))
                   .filter(ContactTask.completed == False, ContactTask.due_date == today)
                   .group_by(ContactTask.assigned_to_id).all())
        to_rows = (db.query(ContactTask.assigned_to_id, func.count(ContactTask.id).label("cnt"))
                   .filter(ContactTask.completed == False, ContactTask.due_date < today)
                   .group_by(ContactTask.assigned_to_id).all())
        tt_map = {r.assigned_to_id: r.cnt for r in tt_rows}
        to_map = {r.assigned_to_id: r.cnt for r in to_rows}
        team_workload = [
            {"id": u.id, "name": u.name,
             "tasks_today":   tt_map.get(u.id, 0),
             "tasks_overdue": to_map.get(u.id, 0)}
            for u in wl_users
        ]
    else:
        tt = (db.query(func.count(ContactTask.id))
              .filter(ContactTask.completed == False,
                      ContactTask.due_date == today,
                      ContactTask.assigned_to_id == uid).scalar() or 0)
        to = (db.query(func.count(ContactTask.id))
              .filter(ContactTask.completed == False,
                      ContactTask.due_date < today,
                      ContactTask.assigned_to_id == uid).scalar() or 0)
        team_workload = [{"id": uid, "name": current_user.name, "tasks_today": tt, "tasks_overdue": to}]

    return {
        "is_admin":              is_admin,
        "total_active_pipeline": total_active,
        "overdue_actions":       overdue_pipeline,
        "total_pipeline_value":  float(total_pipeline_value),
        "commission_due":        float(commission_due),
        "recent_emails": [
            {
                "id":              e.id,
                "subject":         e.subject,
                "direction":       e.direction,
                "contact_name":    e.contact.name    if e.contact else None,
                "contact_company": e.contact.company if e.contact else None,
                "sent_at":         e.sent_at.isoformat() if e.sent_at else None,
            }
            for e in recent_emails
        ],
        "pipeline_by_stage": [
            {"status": r.status, "count": r.cnt, "value": float(r.val or 0)}
            for r in stage_rows
        ],
        "today_actions": [
            {
                "id":              t.ContactTask.id,
                "contact_id":      t.ContactTask.contact_id,
                "title":           t.ContactTask.title,
                "due_date":        t.ContactTask.due_date.isoformat() if t.ContactTask.due_date else None,
                "contact_name":    t.cname,
                "contact_company": t.ccompany,
            }
            for t in today_tasks
        ],
        "team_workload": team_workload,
    }
