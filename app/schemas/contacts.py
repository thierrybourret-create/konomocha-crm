from pydantic import BaseModel
from typing import Optional


class ContactCreate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None
    source: Optional[str] = None


class ContactUpdate(ContactCreate):
    pass


class NoteCreate(BaseModel):
    body: str


class TaskCreate(BaseModel):
    title: str
    due_date: Optional[str] = None
    assigned_to_id: Optional[int] = None


class TaskUpdate(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    due_date: Optional[str] = None


class MergeRequest(BaseModel):
    duplicate_id: int
