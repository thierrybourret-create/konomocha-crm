from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import Brand, User
from app.auth import get_current_user, require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/brands", tags=["brands"])

class BrandCreate(BaseModel):
    name: str
    notes: Optional[str] = None
    is_active: bool = True

def brand_to_dict(b: Brand):
    return {"id": b.id, "name": b.name, "notes": b.notes, "is_active": b.is_active}

@router.get("")
def list_brands(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    brands = db.query(Brand).order_by(Brand.name).all()
    return [brand_to_dict(b) for b in brands]

@router.post("")
def create_brand(data: BrandCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    b = Brand(**data.dict())
    db.add(b)
    db.commit()
    db.refresh(b)
    return brand_to_dict(b)

@router.put("/{brand_id}")
def update_brand(brand_id: int, data: BrandCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    b = db.query(Brand).filter(Brand.id == brand_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Brand not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    return brand_to_dict(b)
