from pydantic import BaseModel
from typing import Optional


class RoleCreate(BaseModel):
    name: str
    permissions: Optional[dict] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[dict] = None
