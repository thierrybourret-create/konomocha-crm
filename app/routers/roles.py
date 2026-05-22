import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import CRMRole, User
from app.auth import require_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/roles", tags=["roles"])

class RoleCreate(BaseModel):
    name: str
    page_access: Optional[list] = None
    report_access: Optional[list] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    page_access: Optional[list] = None
    report_access: Optional[list] = None

def role_to_dict(r: CRMRole):
    return {
        "id":            r.id,
        "name":          r.name,
        "page_access":   json.loads(r.page_access)   if r.page_access   else None,
        "report_access": json.loads(r.report_access) if r.report_access else None,
        "user_count":    len(r.users),
    }

@router.get("")
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return [role_to_dict(r) for r in db.query(CRMRole).order_by(CRMRole.name).all()]

@router.post("")
def create_role(data: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if db.query(CRMRole).filter(CRMRole.name == data.name).first():
        raise HTTPException(status_code=400, detail="Role name already exists")
    r = CRMRole(
        name=data.name,
        page_access=json.dumps(data.page_access) if data.page_access else None,
        report_access=json.dumps(data.report_access) if data.report_access else None,
    )
    db.add(r); db.commit(); db.refresh(r)
    return role_to_dict(r)

@router.put("/{role_id}")
def update_role(role_id: int, data: RoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    r = db.query(CRMRole).filter(CRMRole.id == role_id).first()
    if not r: raise HTTPException(status_code=404, detail="Role not found")
    if data.name: r.name = data.name
    if "page_access" in (data.model_fields_set if hasattr(data,"model_fields_set") else vars(data)):
        r.page_access = json.dumps(data.page_access) if data.page_access else None
    if "report_access" in (data.model_fields_set if hasattr(data,"model_fields_set") else vars(data)):
        r.report_access = json.dumps(data.report_access) if data.report_access else None
    db.commit(); db.refresh(r)
    return role_to_dict(r)

@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    r = db.query(CRMRole).filter(CRMRole.id == role_id).first()
    if not r: raise HTTPException(status_code=404, detail="Role not found")
    if r.users: raise HTTPException(status_code=400, detail=f"{len(r.users)} user(s) assigned to this role — reassign them first")
    db.delete(r); db.commit()
    return {"ok": True}
