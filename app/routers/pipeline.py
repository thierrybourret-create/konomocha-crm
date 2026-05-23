from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, contains_eager
from sqlalchemy import or_, func
from typing import Optional
from decimal import Decimal
from app.database import get_db
from app.models.models import PipelineEntry, Contact, Brand, User, PipelineNote
from app.auth import get_current_user
from app.constants import PIPELINE_PROBABILITIES, COMMISSION_LAG_DAYS
from app.audit import log_audit, diff_and_log, log_created_pipeline, fmt_num, PIPELINE_TRACKED
from app.schemas.pipeline import PipelineCreate, PipelineNoteCreate, PipelineNoteUpdate
from app.permissions import has_scope_all
from app.utils import get_db_probabilities

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


def entry_to_dict(e: PipelineEntry, db: Session = None, prob_map: dict = None):
    if prob_map is None:
        prob_map = get_db_probabilities(db) if db else {}
    prob = prob_map.get(e.status, 0)
    pv = float(e.potential_value) if e.potential_value else 0.0
    fob = e.fob_date.isoformat() if e.fob_date else None
    comm_exp = (e.fob_date + timedelta(days=COMMISSION_LAG_DAYS)).isoformat() if e.fob_date else None
    return {
        "id": e.id,
        "contact_id": e.contact_id,
        "contact_name": e.contact.name if e.contact else None,
        "contact_company": e.contact.company if e.contact else None,
        "brand_id": e.brand_id,
        "brand_name": e.brand.name if e.brand else None,
        "status": e.status,
        "potential_value": pv,
        "probability": prob,
        "weighted_value": round(pv * prob / 100, 2),
        "next_action": e.next_action,
        "fob_date": fob,
        "commission_expected_date": comm_exp,
        "owner_id": e.owner_id,
        "owner_name": e.owner.name if e.owner else None,
        "notes": e.notes,
        "close_reason": e.close_reason,
        "closed_at": e.closed_at.isoformat() if e.closed_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        "last_activity_at": e.last_activity_at.isoformat() if e.last_activity_at else None,
    }

@router.get("/stages")
def get_pipeline_stages(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Public endpoint: returns pipeline stage names + stale_days threshold for all authenticated users."""
    from app.models.models import AppStage
    stages = db.query(AppStage).filter(AppStage.stage_type == 'pipeline').order_by(AppStage.position, AppStage.id).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "label": s.label,
            "probability": s.probability,
            "stale_days": s.stale_days if s.stale_days is not None else 14,
        }
        for s in stages
    ]


@router.get("/probabilities")
def get_probabilities(current_user=Depends(get_current_user)):
    return PIPELINE_PROBABILITIES


@router.get("")
def list_pipeline(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    statuses: Optional[str] = Query(None),
    brand_id: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    contact_id: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("updated_at"),
    sort_dir: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = (
        db.query(PipelineEntry)
        .join(Contact, PipelineEntry.contact_id == Contact.id, isouter=True)
        .join(Brand, PipelineEntry.brand_id == Brand.id, isouter=True)
        .join(User, PipelineEntry.owner_id == User.id, isouter=True)
        .options(
            contains_eager(PipelineEntry.contact),
            contains_eager(PipelineEntry.brand),
            contains_eager(PipelineEntry.owner),
        )
        .filter(PipelineEntry.deleted_at.is_(None))
    )
    if search:
        q = q.filter(or_(
            Contact.name.ilike(f"%{search}%"),
            Contact.company.ilike(f"%{search}%"),
            Brand.name.ilike(f"%{search}%"),
        ))
    if statuses:
        sl = [s.strip() for s in statuses.split(",") if s.strip()]
        if sl:
            q = q.filter(PipelineEntry.status.in_(sl))
    elif status:
        q = q.filter(PipelineEntry.status == status)
    if brand_id:
        q = q.filter(PipelineEntry.brand_id == brand_id)
    if not has_scope_all(current_user, "pipeline"):
        q = q.filter(PipelineEntry.owner_id == current_user.id)
    elif owner_id:
        q = q.filter(PipelineEntry.owner_id == owner_id)
    if contact_id:
        q = q.filter(PipelineEntry.contact_id == contact_id)

    sort_col = {
        "contact":         Contact.company,
        "brand":           Brand.name,
        "status":          PipelineEntry.status,
        "fob_date":        PipelineEntry.fob_date,
        "due_date":        PipelineEntry.fob_date,
        "potential_value": PipelineEntry.potential_value,
        "owner":           User.name,
    }.get(sort_by, PipelineEntry.updated_at)
    q = q.order_by(sort_col.desc() if sort_dir == "desc" else sort_col)

    total = q.count()
    # #17: apply same filters as q; #25: load prob_map once for all rows
    total_value = q.with_entities(func.sum(PipelineEntry.potential_value)).scalar() or 0
    prob_map = get_db_probabilities(db)
    entries = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "total_value": float(total_value),
        "page": page,
        "per_page": per_page,
        "results": [entry_to_dict(e, prob_map=prob_map) for e in entries],
    }


@router.get("/{entry_id}")
def get_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = (
        db.query(PipelineEntry)
        .join(Contact, PipelineEntry.contact_id == Contact.id, isouter=True)
        .join(Brand, PipelineEntry.brand_id == Brand.id, isouter=True)
        .join(User, PipelineEntry.owner_id == User.id, isouter=True)
        .options(
            contains_eager(PipelineEntry.contact),
            contains_eager(PipelineEntry.brand),
            contains_eager(PipelineEntry.owner),
        )
        .filter(PipelineEntry.id == entry_id, PipelineEntry.deleted_at.is_(None))
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry_to_dict(e, db)


@router.post("")
def create_entry(data: PipelineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "agent" and data.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Agents can only create entries assigned to themselves")
    probs = get_db_probabilities(db)
    # #41: reject unknown pipeline statuses
    if probs and data.status not in probs:
        raise HTTPException(status_code=422, detail=f"Unknown pipeline status: '{data.status}'")
    # #37: require close_reason when creating a zero-probability (closed) status entry
    if probs.get(data.status, 1) == 0 and not (data.close_reason or "").strip():
        raise HTTPException(status_code=422, detail="close_reason is required for closed/lost statuses")
    # #39: validate owner_id refers to an existing active user
    if data.owner_id is not None:
        if not db.query(User).filter(User.id == data.owner_id, User.is_active == True).first():
            raise HTTPException(status_code=422, detail="owner_id does not refer to an active user")
    e = PipelineEntry(**data.dict())
    if probs.get(data.status, 1) == 0 and e.closed_at is None:
        e.closed_at = datetime.now(timezone.utc)
    if e.close_reason:
        e.close_reason = e.close_reason.strip() or None
    db.add(e)
    db.commit()
    db.refresh(e)
    log_created_pipeline(db, e, current_user.id, current_user.name)
    db.commit()
    return entry_to_dict(e, db)


@router.put("/{entry_id}")
def update_entry(entry_id: int, data: PipelineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id, PipelineEntry.deleted_at.is_(None)).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    if current_user.role == "agent" and e.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own entries")
    update_data = data.dict(exclude_unset=True)
    close_reason = update_data.pop("close_reason", None)
    old_status = e.status
    new_status = update_data.get("status", old_status)
    # capture snapshot for audit diff
    _snap = {f: getattr(e, f, None) for f in PIPELINE_TRACKED}
    _cname = e.contact.name if e.contact else None
    _bname = e.brand.name   if e.brand   else None
    # #41: reject unknown pipeline statuses on update
    if "status" in update_data:
        probs_check = get_db_probabilities(db)
        if probs_check and update_data["status"] not in probs_check:
            raise HTTPException(status_code=422, detail=f"Unknown pipeline status: '{update_data['status']}'")
    # #39: validate owner_id on update
    if "owner_id" in update_data and update_data["owner_id"] is not None:
        if not db.query(User).filter(User.id == update_data["owner_id"], User.is_active == True).first():
            raise HTTPException(status_code=422, detail="owner_id does not refer to an active user")
    for k, v in update_data.items():
        setattr(e, k, v)
    probs = get_db_probabilities(db)
    if probs.get(new_status, 1) == 0 and probs.get(old_status, 1) != 0:
        if e.closed_at is None:
            e.closed_at = datetime.now(timezone.utc)
    if close_reason is not None:
        e.close_reason = close_reason.strip() or None
    e.last_activity_at = datetime.now(timezone.utc)  # set before commit so it saves in one write
    db.commit()
    db.refresh(e)
    # build new_data including close_reason for diff
    _new_data = dict(update_data)
    if close_reason is not None:
        _new_data['close_reason'] = close_reason
    diff_and_log(db, entity_type='pipeline', entity_id=entry_id,
                 contact_name=_cname, brand_name=_bname,
                 old_obj=type('S', (), _snap)(), new_data=_new_data,
                 tracked_fields=PIPELINE_TRACKED,
                 resolve={'potential_value': fmt_num},
                 user_id=current_user.id, user_name=current_user.name)
    db.commit()
    return entry_to_dict(e, db)


@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    e = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id, PipelineEntry.deleted_at.is_(None)).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    _cname = e.contact.name if e.contact else None
    _bname = e.brand.name   if e.brand   else None
    e.deleted_at = datetime.now(timezone.utc)
    log_audit(db, entity_type='pipeline', entity_id=entry_id,
              contact_name=_cname, brand_name=_bname,
              action='deleted', user_id=current_user.id, user_name=current_user.name)
    db.commit()
    return {"ok": True}


@router.get("/{entry_id}/notes")
def get_pipeline_notes(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id, PipelineEntry.deleted_at.is_(None)).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    notes = db.query(PipelineNote).filter(
        PipelineNote.pipeline_id == entry_id,
        PipelineNote.deleted_at.is_(None)
    ).order_by(PipelineNote.created_at.desc()).all()
    return [{"id": n.id, "body": n.body, "author_name": n.author.name,
             "created_at": n.created_at.isoformat(),
             "updated_at": n.updated_at.isoformat() if n.updated_at else None,
             "updated_by": n.updated_by.name if n.updated_by else None} for n in notes]


@router.post("/{entry_id}/notes")
def add_pipeline_note(entry_id: int, data: PipelineNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id, PipelineEntry.deleted_at.is_(None)).first()
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    note = PipelineNote(pipeline_id=entry_id, body=data.body, author_id=current_user.id)
    db.add(note)
    e.last_activity_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "body": note.body, "author_name": current_user.name,
            "created_at": note.created_at.isoformat(), "updated_at": None, "updated_by": None}


@router.put("/{entry_id}/notes/{note_id}")
def edit_pipeline_note(entry_id: int, note_id: int, data: PipelineNoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import datetime as _dt
    note = db.query(PipelineNote).filter(
        PipelineNote.id == note_id,
        PipelineNote.pipeline_id == entry_id,
        PipelineNote.deleted_at.is_(None)
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
    note.body = data.body
    note.updated_at = _dt.utcnow()
    note.updated_by_id = current_user.id
    db.commit()
    return {"id": note.id, "body": note.body, "author_name": note.author.name,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(), "updated_by": current_user.name}


@router.delete("/{entry_id}/notes/{note_id}")
def delete_pipeline_note(entry_id: int, note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(PipelineNote).filter(
        PipelineNote.id == note_id,
        PipelineNote.pipeline_id == entry_id,
        PipelineNote.deleted_at.is_(None)
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != "admin" and note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    note.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}
