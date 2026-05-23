from pydantic import BaseModel
from typing import Optional


class BrandCreate(BaseModel):
    name: str
    notes: Optional[str] = None
    is_active: bool = True
