from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.database import get_db
from app.models.models import (
    PipelineEntry, Order, EmailLog, ContactNote, ContactTask, AuditLog, User, Contact
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["timeline"])

FIELD_LABEL = {
    "status": "Status", "potential_value": "Value", "close_reason": "Close reason",
    "owner_id": "Owner", "brand_id": "Brand", "fob_date": "FOB date",
    "next_action": "Next action", "order_value": "Order value",
    "gross_commission_rate": "Commission %", "testing_cost_deduction": "Test deduction",
    "order_date": "Order date", "notes": "Notes",
}


def _ts(dt):
    return dt.isoformat() if dt else None


@router.get("/{contact_id}/timeline")
def get_timeline(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = []

    # ── Pipeline entries ───────────────────────────────────────────────────
    pipeline_entries = (
        db.query(PipelineEntry)
        .options(joinedload(PipelineEntry.brand), joinedload(PipelineEntry.owner))
        .filter(PipelineEntry.contact_id == contact_id)
        .all()
    )
    pipeline_ids = [e.id for e in pipeline_entries]

    for e in pipeline_entries:
        bname = e.brand.name if e.brand else ""
        oname = e.owner.name if e.owner else ""
        val   = "{:,.2f}".format(float(e.potential_value)) if e.potential_value else "0.00"
        events.append({
            "type":      "pipeline_created",
            "timestamp": _ts(e.created_at),
            "icon":      "pipeline",
            "title":     "Pipeline entry created",
            "detail":    f"{bname} — Status: {e.status} · Value: ${val}",
            "actor":     oname,
            "entity_id": e.id,
        })
        if e.deleted_at:
            events.append({
                "type":      "pipeline_deleted",
                "timestamp": _ts(e.deleted_at),
                "icon":      "pipeline",
                "title":     "Pipeline entry deleted",
                "detail":    bname,
                "actor":     None,
                "entity_id": e.id,
            })

    # ── Orders ────────────────────────────────────────────────────────────
    orders = (
        db.query(Order)
        .options(joinedload(Order.brand), joinedload(Order.owner))
        .filter(Order.contact_id == contact_id)
        .all()
    )
    order_ids = [o.id for o in orders]

    for o in orders:
        bname = o.brand.name if o.brand else ""
        oname = o.owner.name if o.owner else ""
        val   = "{:,.2f}".format(float(o.order_value)) if o.order_value else "0.00"
        events.append({
            "type":      "order_created",
            "timestamp": _ts(o.created_at),
            "icon":      "order",
            "title":     "Order created",
            "detail":    f"{bname} — Value: ${val} · Status: {o.status}",
            "actor":     oname,
            "entity_id": o.id,
        })

    # ── Audit log (updates & deletes only — creates come from tables above) ─
    if pipeline_ids or order_ids:
        conditions = []
        if pipeline_ids:
            conditions.append(
                (AuditLog.entity_type == "pipeline") &
                (AuditLog.entity_id.in_(pipeline_ids))
            )
        if order_ids:
            conditions.append(
                (AuditLog.entity_type == "order") &
                (AuditLog.entity_id.in_(order_ids))
            )
        audit_rows = (
            db.query(AuditLog)
            .filter(or_(*conditions), AuditLog.action == "updated")
            .all()
        )
        for a in audit_rows:
            etype = a.entity_type
            fl    = FIELD_LABEL.get(a.field_name, a.field_name or "")
            if a.field_name == "status":
                detail = f"{a.brand_name or ''} — {a.old_value or '?'} → {a.new_value or '?'}"
                title  = "Pipeline status changed" if etype == "pipeline" else "Order status advanced"
            else:
                detail = f"{a.brand_name or ''} — {fl}: {a.old_value or '?'} → {a.new_value or '?'}"
                title  = "Pipeline updated" if etype == "pipeline" else "Order updated"
            events.append({
                "type":      f"{etype}_updated",
                "timestamp": _ts(a.created_at),
                "icon":      etype,
                "title":     title,
                "detail":    detail.strip(" —"),
                "actor":     a.user_name,
                "entity_id": a.entity_id,
            })

    # ── Email logs ────────────────────────────────────────────────────────
    emails = (
        db.query(EmailLog)
        .options(joinedload(EmailLog.logged_by))
        .filter(EmailLog.contact_id == contact_id)
        .all()
    )
    for em in emails:
        direction = "received" if em.direction and em.direction.value == "inbound" else "sent"
        events.append({
            "type":      "email",
            "timestamp": _ts(em.sent_at),
            "icon":      "email",
            "title":     f"Email {direction}",
            "detail":    em.subject or "(no subject)",
            "actor":     em.logged_by.name if em.logged_by else None,
            "entity_id": em.id,
        })

    # ── Contact notes ─────────────────────────────────────────────────────
    notes = (
        db.query(ContactNote)
        .options(joinedload(ContactNote.author))
        .filter(ContactNote.contact_id == contact_id, ContactNote.deleted_at.is_(None))
        .all()
    )
    for n in notes:
        events.append({
            "type":      "note",
            "timestamp": _ts(n.created_at),
            "icon":      "note",
            "title":     "Note added",
            "detail":    (n.body or "")[:200],
            "actor":     n.author.name if n.author else None,
            "entity_id": n.id,
        })

    # ── Imported note (contact.notes field — historical data) ──────────────
    contact_obj = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact_obj and contact_obj.notes:
        events.append({
            "type":      "note",
            "timestamp": None,
            "icon":      "note",
            "title":     "Imported note",
            "detail":    (contact_obj.notes or "")[:300],
            "actor":     None,
            "entity_id": None,
        })

    # ── Tasks ─────────────────────────────────────────────────────────────
    tasks = (
        db.query(ContactTask)
        .options(joinedload(ContactTask.created_by), joinedload(ContactTask.assigned_to))
        .filter(ContactTask.contact_id == contact_id)
        .all()
    )
    for t in tasks:
        events.append({
            "type":      "task",
            "timestamp": _ts(t.created_at),
            "icon":      "task",
            "title":     "Task created",
            "detail":    t.title,
            "actor":     t.created_by.name if t.created_by else None,
            "entity_id": t.id,
        })
        if t.completed_at:
            events.append({
                "type":      "task_done",
                "timestamp": _ts(t.completed_at),
                "icon":      "task_done",
                "title":     "Task completed",
                "detail":    t.title,
                "actor":     t.assigned_to.name if t.assigned_to else None,
                "entity_id": t.id,
            })

    # ── Sort newest first ─────────────────────────────────────────────────
    events.sort(key=lambda x: x["timestamp"] or "", reverse=True)

    return {"total": len(events), "events": events}
