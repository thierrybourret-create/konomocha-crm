import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, UserRole, CRMRole
from app.auth import require_admin, hash_password
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/users", tags=["users"])

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = UserRole.agent
    role_id: Optional[int] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    role_id: Optional[int] = None

def user_to_dict(u: User):
    crm = None
    if u.crm_role:
        perms = None
        if u.crm_role.permissions:
            try: perms = json.loads(u.crm_role.permissions)
            except: pass
        crm = {"id": u.crm_role.id, "name": u.crm_role.name, "permissions": perms}
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role,
            "is_active": u.is_active, "role_id": u.role_id, "crm_role": crm}

@router.get("")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return [user_to_dict(u) for u in db.query(User).all()]

@router.post("")
def create_user(data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(name=data.name, email=data.email, hashed_password=hash_password(data.password),
             role=data.role, role_id=data.role_id or None)
    db.add(u); db.commit(); db.refresh(u)
    return user_to_dict(u)

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="User not found")
    if data.name:     u.name  = data.name
    if data.email:    u.email = data.email
    if data.role:     u.role  = data.role
    if data.password: u.hashed_password = hash_password(data.password)
    fields = data.model_fields_set if hasattr(data, 'model_fields_set') else set(vars(data).keys())
    if 'role_id' in fields:
        u.role_id = data.role_id or None
    db.commit(); db.refresh(u)
    return user_to_dict(u)

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="User not found")
    db.delete(u); db.commit()
    return {"ok": True}
