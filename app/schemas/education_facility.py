from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EducationFacilityBase(BaseModel):
    name: str
    icon: Optional[str] = None
    country: Optional[str] = None

class EducationFacilityCreate(EducationFacilityBase):
    pass

class EducationFacilityUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    country: Optional[str] = None

class EducationFacilityResponse(EducationFacilityBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EducationFacilityListResponse(BaseModel):
    facilities: list[EducationFacilityResponse]
    total: int
    skip: int
    limit: int
