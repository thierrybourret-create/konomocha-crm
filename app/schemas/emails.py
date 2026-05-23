from pydantic import BaseModel
from typing import Optional


class EmailCreate(BaseModel):
    direction: str
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    subject: Optional[str] = None
    body_snippet: Optional[str] = None
    sent_at: Optional[str] = None
    raw_message_id: Optional[str] = None
    bcc_address: Optional[str] = None
