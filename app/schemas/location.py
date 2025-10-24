from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LocationBase(BaseModel):
    name: str
    flag_image: Optional[str] = None
    code: Optional[str] = None
    phone_code: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    flag_image: Optional[str] = None
    code: Optional[str] = None
    phone_code: Optional[str] = None

class Location(LocationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    
    class Config:
        from_attributes = True 