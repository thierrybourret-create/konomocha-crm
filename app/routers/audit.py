from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.models import AuditLog, User
from app.auth import get_current_user

router = APIRouter(prefix='/api/audit-log', tags=['audit'])


@router.get('')
def get_audit_log(
    entity_type: Optional[str] = Query(None),  # 'pipeline' | 'order' | None=all
    user_id:     Optional[int]  = Query(None),
    date_from:   Optional[date] = Query(None),
    date_to:     Optional[date] = Query(None),
    page:        int            = Query(1, ge=1),
    per_page:    int            = Query(100, ge=1, le=1000),
    db:          Session        = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    if current_user.role != 'admin':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail='Admin only')

    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        from datetime import datetime, timedelta
        q = q.filter(AuditLog.created_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))

    total = q.count()
    rows  = q.order_by(desc(AuditLog.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    return {
        'total':   total,
        'page':    page,
        'per_page': per_page,
        'results': [
            {
                'id':           r.id,
                'entity_type':  r.entity_type,
                'entity_id':    r.entity_id,
                'contact_name': r.contact_name,
                'brand_name':   r.brand_name,
                'action':       r.action,
                'field_name':   r.field_name,
                'old_value':    r.old_value,
                'new_value':    r.new_value,
                'user_name':    r.user_name,
                'created_at':   r.created_at.isoformat(),
            }
            for r in rows
        ],
    }
