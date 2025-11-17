from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .corporate_profile import CorporateProfileResponse
from .profile import UserFullResponse


class CorporateProfileFollowCreate(BaseModel):
    """Schema for creating a corporate profile follow"""
    corporate_profile_id: int = Field(..., description="ID of the corporate profile to follow")

    class Config:
        json_schema_extra = {
            "example": {
                "corporate_profile_id": 1
            }
        }


class CorporateProfileFollowResponse(BaseModel):
    """Schema for corporate profile follow response"""
    id: int
    user_id: int
    corporate_profile_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "corporate_profile_id": 1,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class CorporateProfileFollowDetailedResponse(BaseModel):
    """Schema for follow response with full corporate profile details"""
    id: int
    corporate_profile: CorporateProfileResponse
    created_at: datetime

    class Config:
        from_attributes = True


class CorporateProfileFollowerResponse(BaseModel):
    """Schema for follower response with full user details"""
    id: int
    user: UserFullResponse
    created_at: datetime

    class Config:
        from_attributes = True


class CorporateProfileFollowListResponse(BaseModel):
    """Schema for paginated following list response"""
    items: list[CorporateProfileFollowDetailedResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


class CorporateProfileFollowerListResponse(BaseModel):
    """Schema for paginated followers list response"""
    items: list[CorporateProfileFollowerResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True

