from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.database import get_db
from app.models.models import ContactTask, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("")
def list_tasks(
    assignee_me: bool = Query(False),
    completed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(ContactTask).options(
        joinedload(ContactTask.contact),
        joinedload(ContactTask.assigned_to),
        joinedload(ContactTask.created_by),
    )
    if assignee_me:
        q = q.filter(ContactTask.assigned_to_id == current_user.id)
    if completed is not None:
        q = q.filter(ContactTask.completed == completed)
    from sqlalchemy import asc, nullslast
    q = q.order_by(nullslast(asc(ContactTask.due_date)), ContactTask.created_at.asc())
    tasks = q.all()
    return [
        {
            "id": t.id,
            "contact_id": t.contact_id,
            "contact_name": t.contact.name if t.contact else None,
            "contact_company": t.contact.company if t.contact else None,
            "title": t.title,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed": t.completed,
            "assigned_to": t.assigned_to.name if t.assigned_to else None,
            "created_by": t.created_by.name if t.created_by else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in tasks
    ]
