from pydantic import BaseModel
from typing import Optional
from app.models.models import UserRole


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
