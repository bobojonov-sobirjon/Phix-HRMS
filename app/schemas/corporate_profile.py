from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CompanySize(str, Enum):
    STARTUP = "1-10"
    SMALL = "10-50"
    MEDIUM = "50-200"
    LARGE = "200-1000"
    ENTERPRISE = "1000+"


# Company schema for response
class CompanyResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    country: Optional[str] = None
    
    class Config:
        from_attributes = True


# Category schema for response
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


# Base schema
class CorporateProfileBase(BaseModel):
    phone_number: str
    country_code: str = "+1"
    location_id: int
    overview: str
    website_url: Optional[str] = None
    company_size: CompanySize
    logo_url: Optional[str] = None
    category_id: Optional[int] = None
    company_id: Optional[int] = None


# Create schema
class CorporateProfileCreate(CorporateProfileBase):
    pass


# Update schema
class CorporateProfileUpdate(BaseModel):
    phone_number: Optional[str] = None
    country_code: Optional[str] = None
    location_id: Optional[int] = None
    overview: Optional[str] = None
    website_url: Optional[str] = None
    company_size: Optional[CompanySize] = None
    logo_url: Optional[str] = None
    category_id: Optional[int] = None
    company_id: Optional[int] = None


# Location schema for response
class LocationResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    flag_image: Optional[str] = None
    phone_code: Optional[str] = None
    
    class Config:
        from_attributes = True


# User schema for response
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    is_verified: bool
    is_social_user: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    location_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Team member schema for response
class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    user_avatar: Optional[str] = None
    role: str
    status: str
    invited_by_user_id: int
    invited_by_name: str
    created_at: datetime
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Response schema
class CorporateProfileResponse(CorporateProfileBase):
    id: int
    user_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    location: Optional[LocationResponse] = None
    user: Optional[UserResponse] = None
    company: Optional[CompanyResponse] = None
    category: Optional[CategoryResponse] = None
    team_members: List[TeamMemberResponse] = []
    is_followed: Optional[bool] = False
    followers_count: int = Field(default=0, description="Number of followers for this corporate profile")
    follow_relation_id: Optional[int] = Field(default=None, description="ID of the follow relationship (if user is following)")
    
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
