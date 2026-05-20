from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional
import io, csv
from app.database import get_db
from app.models.models import Contact, PipelineEntry, Order, EmailLog, User, ContactNote, ContactTask
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/reports", tags=["reports"])

DEF_REGIONS = ['Africa','Asia','Balkans','Eastern Europe','Europe','India','Middle East',
                'North America','Oceania','South America']

DEF_COUNTRIES = [
    'Afghanistan','Albania','Algeria','Argentina','Australia','Austria',
    'Bahrain','Bangladesh','Belgium','Brazil','Bulgaria','Cambodia','Canada',
    'Chile','China','Colombia','Croatia','Cyprus','Czech Republic','Denmark',
    'Ecuador','Egypt','Estonia','Fiji','Finland','France','Georgia','Germany','Ghana',
    'Gibraltar','Greece','Hong Kong','Hungary','India','Indonesia','Iran','Iraq','Ireland',
    'Israel','Italy','Japan','Jordan','Kazakhstan','Kenya','Kuwait','Latvia',
    'Lebanon','Lithuania','Luxembourg','Malaysia','Malta','Mexico','Morocco',
    'Netherlands','New Zealand','Nigeria','Norway','Oman','Pakistan','Philippines',
    'Poland','Portugal','Qatar','Romania','Russia','Saudi Arabia','Singapore',
    'Slovakia','Slovenia','South Africa','South Korea','Spain','Sri Lanka',
    'Angola','Armenia','Azerbaijan','Belarus','Bosnia','Botswana',
    'Costa Rica','Dominican Republic','El Salvador',
    'Iceland','Jamaica','Korea','Liechtenstein',
    'Macedonia','Madagascar','Mauritius','Moldova','Mongolia','Myanmar',
    'Namibia','Panama','Palestine','Paraguay','Peru','Puerto Rico',
    'Senegal','Serbia','Sweden','Switzerland',
    'Taiwan','Thailand','Trinidad and Tobago','Tunisia','Turkey',
    'Ukraine','United Arab Emirates','United Kingdom',
    'United States of America','Uruguay','Venezuela','Vietnam','Zimbabwe',
]

DEF_TAGS = ['Agent','CloseOut','DND','Distributor','Manufacturer','Network','Principal','Retailer','Stationery']

def _has_region(tags):
    if not tags: return False
    return any(r in tags for r in DEF_REGIONS)

def _has_group(tags):
    if not tags: return False
    parts = [t.strip() for t in tags.split(',') if t.strip()]
    return any(t for t in parts if t not in DEF_REGIONS and t not in ('Contact', 'Company'))

def _get_region(tags):
    if not tags: return None
    for r in DEF_REGIONS:
        if r in tags: return r
    return None

def _score(c):
    checks = [
        bool(c.email   and c.email.strip()),
        bool(c.phone   and c.phone.strip()),
        bool(c.country and c.country.strip()),
        _has_region(c.tags),
        _has_group(c.tags),
    ]
    score = int(sum(checks) / len(checks) * 100)
    missing = []
    labels  = ['Email','Phone','Country','Region','Tags']
    for ok, lbl in zip(checks, labels):
        if not ok: missing.append(lbl)
    return score, missing

def _row(c):
    score, missing = _score(c)
    has_region      = _has_region(c.tags)
    has_country     = bool(c.country and c.country.strip())
    wrong_region    = has_country and not has_region
    invalid_country = has_country and c.country.strip() not in DEF_COUNTRIES
    return {
        "id":              c.id,
        "name":            c.name or "",
        "company":         c.company or "",
        "email":           c.email or "",
        "phone":           c.phone or "",
        "country":         c.country or "",
        "region":          _get_region(c.tags) or "",
        "tags":            c.tags or "",
        "score":           score,
        "missing":         missing,
        "wrong_region":    wrong_region,
        "invalid_country": invalid_country,
        "complete":        score == 100,
        "owner":           c.owner.name if c.owner else "",
    }

@router.get("/contact-quality")
def contact_quality(
    filter:       str = Query("all"),
    search:       str = Query(""),
    owner_id:     Optional[int] = Query(None),
    contact_type: str = Query("contacts"),   # contacts | companies | all
    page:         int = Query(1, ge=1),
    per_page:     int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    q = db.query(Contact)
    if contact_type == "contacts":
        q = q.filter(Contact.source.notin_(("lacrm_company_import", "pipeline_import")))
    elif contact_type == "companies":
        q = q.filter(Contact.source.in_(("lacrm_company_import", "pipeline_import")))

    if search:
        s = f"%{search}%"
        q = q.filter(or_(Contact.name.ilike(s), Contact.company.ilike(s), Contact.email.ilike(s)))

    if owner_id:
        q = q.filter(Contact.owner_id == owner_id)

    contacts = q.all()
    all_rows = [_row(c) for c in contacts]

    total            = len(all_rows)
    n_missing        = sum(1 for r in all_rows if not r["complete"])
    n_complete       = sum(1 for r in all_rows if r["complete"])
    n_wrong_rgn      = sum(1 for r in all_rows if r["wrong_region"])
    n_invalid_ctry   = sum(1 for r in all_rows if r["invalid_country"])

    if filter == "missing":
        filtered = [r for r in all_rows if not r["complete"]]
    elif filter == "complete":
        filtered = [r for r in all_rows if r["complete"]]
    elif filter == "wrong_region":
        filtered = [r for r in all_rows if r["wrong_region"]]
    elif filter == "invalid_country":
        filtered = [r for r in all_rows if r["invalid_country"]]
    else:
        filtered = all_rows

    filtered.sort(key=lambda r: r["score"])
    start     = (page - 1) * per_page
    page_rows = filtered[start:start + per_page]

    return {
        "total":             total,
        "n_missing":         n_missing,
        "n_complete":        n_complete,
        "n_wrong_region":    n_wrong_rgn,
        "n_invalid_country": n_invalid_ctry,
        "filtered_total":    len(filtered),
        "page":              page,
        "per_page":          per_page,
        "results":           page_rows,
    }

@router.get("/contact-quality-csv")
def contact_quality_csv(
    filter:       str = Query("all"),
    search:       str = Query(""),
    owner_id:     Optional[int] = Query(None),
    contact_type: str = Query("contacts"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    q = db.query(Contact)
    if contact_type == "contacts":
        q = q.filter(Contact.source.notin_(("lacrm_company_import", "pipeline_import")))
    elif contact_type == "companies":
        q = q.filter(Contact.source.in_(("lacrm_company_import", "pipeline_import")))

    if search:
        s = f"%{search}%"
        q = q.filter(or_(Contact.name.ilike(s), Contact.company.ilike(s), Contact.email.ilike(s)))

    if owner_id:
        q = q.filter(Contact.owner_id == owner_id)

    contacts = q.all()
    all_rows = [_row(c) for c in contacts]

    if filter == "missing":
        rows = [r for r in all_rows if not r["complete"]]
    elif filter == "complete":
        rows = [r for r in all_rows if r["complete"]]
    elif filter == "wrong_region":
        rows = [r for r in all_rows if r["wrong_region"]]
    elif filter == "invalid_country":
        rows = [r for r in all_rows if r["invalid_country"]]
    else:
        rows = all_rows

    rows.sort(key=lambda r: r["score"])

    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["Name","Company","Email","Phone","Country","Region","Owner","Score","Missing Fields","Status"])
    for r in rows:
        w.writerow([
            r["name"], r["company"], r["email"], r["phone"],
            r["country"], r["region"], r["owner"], f"{r['score']}%",
            ", ".join(r["missing"]),
            "Complete" if r["complete"] else "Missing fields",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contact_quality.csv"},
    )

@router.get("/activity")
def activity_report(
    period: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    deltas = {"1d":1,"7d":7,"30d":30,"90d":90,"365d":365}
    start = datetime.utcnow() - timedelta(days=deltas.get(period, 30))
    return {
        "period":               period,
        "since":                start.date().isoformat(),
        "new_contacts":         db.query(Contact).filter(Contact.source.notin_(("lacrm_company_import", "pipeline_import")), Contact.created_at >= start).count(),
        "new_companies":        db.query(Contact).filter(Contact.source.in_(("lacrm_company_import", "pipeline_import")), Contact.created_at >= start).count(),
        "new_pipeline_entries": db.query(PipelineEntry).filter(PipelineEntry.created_at >= start).count(),
        "new_orders":           db.query(Order).filter(Order.created_at >= start).count(),
        "emails_inbound":       db.query(EmailLog).filter(EmailLog.sent_at >= start, EmailLog.direction == "inbound").count(),
        "emails_outbound":      db.query(EmailLog).filter(EmailLog.sent_at >= start, EmailLog.direction == "outbound").count(),
        "new_tasks":            db.query(ContactTask).filter(ContactTask.created_at >= start).count(),
        "new_notes":            db.query(ContactNote).filter(ContactNote.created_at >= start).count(),
    }


@router.get("/tasks")
def task_report(
    filter: str = Query("open"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    from app.models.models import ContactTask
    from datetime import date
    q = db.query(ContactTask)
    today = date.today()
    if filter == "open":
        q = q.filter(ContactTask.completed == False)
    elif filter == "overdue":
        q = q.filter(ContactTask.completed == False, ContactTask.due_date < today)
    elif filter == "completed":
        q = q.filter(ContactTask.completed == True)
    tasks = q.order_by(ContactTask.due_date.asc().nullslast(), ContactTask.created_at.desc()).all()
    return [{"id": t.id, "title": t.title,
             "due_date": t.due_date.isoformat() if t.due_date else None,
             "completed": t.completed,
             "contact_id": t.contact_id,
             "contact_name": t.contact.name if t.contact else None,
             "contact_company": t.contact.company if t.contact else None,
             "assigned_to": t.assigned_to.name if t.assigned_to else None,
             "created_by": t.created_by.name if t.created_by else None,
             "created_at": t.created_at.isoformat()} for t in tasks]
