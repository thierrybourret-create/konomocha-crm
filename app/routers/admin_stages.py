from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import AppStage, User
from app.auth import get_current_user

router = APIRouter(prefix="/admin/stages", tags=["admin-stages"])


class StageCreate(BaseModel):
    stage_type: str          # 'pipeline' or 'order'
    name: str
    label: str
    probability: Optional[int] = None
    position: Optional[int] = None


class StageUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    probability: Optional[int] = None
    position: Optional[int] = None


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("")
def get_stages(db: Session = Depends(get_db), _=Depends(require_admin)):
    stages = db.query(AppStage).order_by(
        AppStage.stage_type, AppStage.position, AppStage.id
    ).all()
    return {
        "pipeline": [
            {"id": s.id, "name": s.name, "label": s.label,
              "probability": s.probability, "position": s.position}
            for s in stages if s.stage_type == 'pipeline'
        ],
        "order": [
            {"id": s.id, "name": s.name, "label": s.label,
              "probability": s.probability, "position": s.position}
            for s in stages if s.stage_type == 'order'
        ],
    }


@router.post("")
def create_stage(
    data: StageCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if data.stage_type not in ('pipeline', 'order'):
        raise HTTPException(400, "stage_type must be 'pipeline' or 'order'")
    max_pos = db.query(AppStage).filter(AppStage.stage_type == data.stage_type).count()
    stage = AppStage(
        stage_type=data.stage_type,
        name=data.name,
        label=data.label,
        probability=data.probability,
        position=data.position if data.position is not None else max_pos,
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return {
        "id": stage.id, "name": stage.name, "label": stage.label,
        "probability": stage.probability, "position": stage.position,
    }


@router.put("/{stage_id}")
def update_stage(
    stage_id: int,
    data: StageUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    stage = db.query(AppStage).filter(AppStage.id == stage_id).first()
    if not stage:
        raise HTTPException(404, "Stage not found")
    if data.name is not None:
        stage.name = data.name
    if data.label is not None:
        stage.label = data.label
    if data.probability is not None:
        stage.probability = data.probability
    if data.position is not None:
        stage.position = data.position
    db.commit()
    return {
        "id": stage.id, "name": stage.name, "label": stage.label,
        "probability": stage.probability, "position": stage.position,
    }


@router.delete("/{stage_id}")
def delete_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    stage = db.query(AppStage).filter(AppStage.id == stage_id).first()
    if not stage:
        raise HTTPException(404, "Stage not found")
    db.delete(stage)
    db.commit()
    return {"ok": True}
