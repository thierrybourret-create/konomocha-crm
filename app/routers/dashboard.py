from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from app.database import get_db
from app.models.models import PipelineEntry, Order, EmailLog, User, ContactTask, Contact, Brand, AppStage
from app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today    = date.today()
    is_admin = getattr(current_user, "role", None) == "admin"
    uid      = current_user.id

    # ── Pipeline stages from DB ───────────────────────────────────────────────
    pipeline_stages    = db.query(AppStage).filter(AppStage.stage_type == 'pipeline').all()
    stage_prob_map     = {s.name: (s.probability or 0) for s in pipeline_stages}
    stage_stale_map    = {s.name: (s.stale_days or 14)  for s in pipeline_stages}
    active_stage_names = [name for name, prob in stage_prob_map.items() if prob > 0]

    # ── Pipeline KPIs ─────────────────────────────────────────────────────────
    pq = db.query(PipelineEntry).filter(PipelineEntry.status.in_(active_stage_names))
    if not is_admin:
        pq = pq.filter(PipelineEntry.owner_id == uid)

    total_active     = pq.count()
    overdue_pipeline = pq.filter(PipelineEntry.fob_date < today).count()

    # Weighted pipeline value: potential_value x (stage_probability / 100)
    val_entries = db.query(PipelineEntry.status, PipelineEntry.potential_value)\
        .filter(PipelineEntry.status.in_(active_stage_names))
    if not is_admin:
        val_entries = val_entries.filter(PipelineEntry.owner_id == uid)
    total_pipeline_value = sum(
        float(row.potential_value or 0) * stage_prob_map.get(row.status, 0) / 100
        for row in val_entries.all()
    )

    # ── Commission due (via order owner) ──────────────────────────────────────
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
          .filter(PipelineEntry.status.in_(active_stage_names)))
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

    # ── Team workload ──────────────────────────────────────────────────────────
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

    # ── Stale deals (server-side; avoids expensive client-side full pipeline fetch) ─
    _now = datetime.utcnow()
    stale_q = (
        db.query(
            PipelineEntry.id,
            PipelineEntry.status,
            PipelineEntry.last_activity_at,
            PipelineEntry.updated_at,
            Contact.name.label('cname'),
            Contact.company.label('ccompany'),
            Brand.name.label('bname'),
        )
        .join(Contact, PipelineEntry.contact_id == Contact.id, isouter=True)
        .join(Brand,   PipelineEntry.brand_id   == Brand.id,   isouter=True)
        .filter(
            PipelineEntry.status.in_(active_stage_names),
            PipelineEntry.deleted_at.is_(None),
            PipelineEntry.closed_at.is_(None),
        )
    )
    if not is_admin:
        stale_q = stale_q.filter(PipelineEntry.owner_id == uid)
    stale_list = []
    for row in stale_q.all():
        act_ts    = row.last_activity_at or row.updated_at
        days_idle = int((_now - act_ts).total_seconds() // 86400) if act_ts else 0
        threshold = stage_stale_map.get(row.status, 14)
        pct       = days_idle / threshold if threshold > 0 else 0
        if pct >= 0.75:
            stale_list.append({
                'id':              row.id,
                'contact_name':    row.cname,
                'contact_company': row.ccompany,
                'brand_name':      row.bname,
                'status':          row.status,
                'days_idle':       days_idle,
                'stale_days':      threshold,
            })
    stale_list.sort(key=lambda x: x['days_idle'], reverse=True)

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
            {"status": r.status, "count": r.cnt, "value": float(r.val or 0),
             "probability": stage_prob_map.get(r.status, 0)}
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
        "stale_count":   len(stale_list),
        "stale_deals":   stale_list[:8],
    }
