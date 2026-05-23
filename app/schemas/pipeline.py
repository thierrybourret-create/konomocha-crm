from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import date


class PipelineCreate(BaseModel):
    contact_id: int
    brand_id: int
    status: str
    potential_value: Decimal
    next_action: Optional[str] = None
    fob_date: Optional[date] = None
    owner_id: int
    notes: Optional[str] = None
    close_reason: Optional[str] = None


class PipelineNoteCreate(BaseModel):
    body: str


class PipelineNoteUpdate(BaseModel):
    body: str
