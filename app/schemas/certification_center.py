from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CertificationCenterBase(BaseModel):
    name: str
    icon: Optional[str] = None

class CertificationCenterCreate(CertificationCenterBase):
    pass

class CertificationCenterUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None

class CertificationCenterResponse(CertificationCenterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CertificationCenterListResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None

    class Config:
        from_attributes = True

