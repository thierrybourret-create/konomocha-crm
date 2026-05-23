from pydantic import BaseModel, Field
from typing import Optional


class StageCreate(BaseModel):
    stage_type: str  # 'pipeline' or 'order'
    name: str
    label: str
    probability: Optional[int] = None
    position: Optional[int] = None
    stale_days: Optional[int] = Field(None, ge=1, le=3650)


class StageUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    probability: Optional[int] = None
    position: Optional[int] = None
    stale_days: Optional[int] = Field(None, ge=1, le=3650)
