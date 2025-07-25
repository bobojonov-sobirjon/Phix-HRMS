from pydantic import BaseModel
from typing import Optional

class LanguageBase(BaseModel):
    name: str

class LanguageCreate(LanguageBase):
    pass

class LanguageUpdate(LanguageBase):
    name: Optional[str] = None

class LanguageResponse(LanguageBase):
    id: int
    class Config:
        from_attributes = True 