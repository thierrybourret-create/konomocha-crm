import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import CRMRole, User
from app.auth import require_admin
from app.schemas.roles import RoleCreate, RoleUpdate

router = APIRouter(prefix="/api/roles", tags=["roles"])

def role_to_dict(r: CRMRole):
    perms = None
    if r.permissions:
        try: perms = json.loads(r.permissions)
        except: pass
    return {"id": r.id, "name": r.name, "permissions": perms, "user_count": len(r.users)}

@router.get("")
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return [role_to_dict(r) for r in db.query(CRMRole).order_by(CRMRole.name).all()]

@router.post("")
def create_role(data: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if db.query(CRMRole).filter(CRMRole.name == data.name).first():
        raise HTTPException(status_code=400, detail="Role name already exists")
    r = CRMRole(name=data.name, permissions=json.dumps(data.permissions) if data.permissions is not None else None)
    db.add(r); db.commit(); db.refresh(r)
    return role_to_dict(r)

@router.put("/{role_id}")
def update_role(role_id: int, data: RoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    r = db.query(CRMRole).filter(CRMRole.id == role_id).first()
    if not r: raise HTTPException(status_code=404, detail="Role not found")
    if data.name is not None: r.name = data.name
    fields = data.model_fields_set if hasattr(data, 'model_fields_set') else set(vars(data).keys())
    if 'permissions' in fields:
        r.permissions = json.dumps(data.permissions) if data.permissions else None
    db.commit(); db.refresh(r)
    return role_to_dict(r)

@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    r = db.query(CRMRole).filter(CRMRole.id == role_id).first()
    if not r: raise HTTPException(status_code=404, detail="Role not found")
    if r.users: raise HTTPException(status_code=400, detail=f"{len(r.users)} user(s) assigned — reassign first")
    db.delete(r); db.commit()
    return {"ok": True}
