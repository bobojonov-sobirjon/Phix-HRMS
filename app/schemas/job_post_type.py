from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobPostTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class JobPostTypeCreate(JobPostTypeBase):
    pass

class JobPostTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class JobPostType(JobPostTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    
    class Config:
        from_attributes = True 