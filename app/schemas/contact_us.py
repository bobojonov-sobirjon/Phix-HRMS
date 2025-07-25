from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ContactUsBase(BaseModel):
    name: str
    contact_type: str
    value: str

class ContactUsCreate(ContactUsBase):
    pass

class ContactUsUpdate(BaseModel):
    name: Optional[str] = None
    contact_type: Optional[str] = None
    value: Optional[str] = None

class ContactUsOut(ContactUsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True 