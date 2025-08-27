from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CompanySize(str, Enum):
    STARTUP = "1-10"
    SMALL = "10-50"
    MEDIUM = "50-200"
    LARGE = "200-1000"
    ENTERPRISE = "1000+"


# Base schema
class CorporateProfileBase(BaseModel):
    company_name: str
    industry: str
    phone_number: str
    country_code: str = "+1"
    location: str
    overview: str
    website_url: Optional[str] = None
    company_size: CompanySize
    logo_url: Optional[str] = None


# Create schema
class CorporateProfileCreate(CorporateProfileBase):
    pass


# Update schema
class CorporateProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    phone_number: Optional[str] = None
    country_code: Optional[str] = None
    location: Optional[str] = None
    overview: Optional[str] = None
    website_url: Optional[str] = None
    company_size: Optional[CompanySize] = None
    logo_url: Optional[str] = None


# Response schema
class CorporateProfileResponse(CorporateProfileBase):
    id: int
    user_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Verification schema
class CorporateProfileVerification(BaseModel):
    otp_code: str


# List response schema
class CorporateProfileListResponse(BaseModel):
    corporate_profiles: List[CorporateProfileResponse]
    total: int
    page: int
    size: int
