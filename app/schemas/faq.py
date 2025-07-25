from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FAQBase(BaseModel):
    question: str
    answer: str

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None

class FAQOut(FAQBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True 