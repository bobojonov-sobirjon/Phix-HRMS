from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .profile import UserFullResponse
from .gig_job import GigJobResponse
from .full_time_job import FullTimeJobResponse


class SavedJobCreate(BaseModel):
    """Schema for creating a saved job"""
    gig_job_id: Optional[int] = Field(None, description="ID of the gig job to save")
    full_time_job_id: Optional[int] = Field(None, description="ID of the full-time job to save")

    class Config:
        json_schema_extra = {
            "example": {
                "gig_job_id": 1,
                "full_time_job_id": None
            }
        }


class SavedJobResponse(BaseModel):
    """Schema for saved job response"""
    id: int
    user_id: int
    gig_job_id: Optional[int] = None
    full_time_job_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "gig_job_id": 1,
                "full_time_job_id": None,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class SavedJobDetailedResponse(BaseModel):
    """Schema for saved job response with full details"""
    id: int
    user_id: int
    gig_job_id: Optional[int] = None
    full_time_job_id: Optional[int] = None
    created_at: datetime
    
    # Full details
    user: Optional[UserFullResponse] = None
    gig_job: Optional[GigJobResponse] = None
    full_time_job: Optional[FullTimeJobResponse] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "gig_job_id": 1,
                "full_time_job_id": None,
                "created_at": "2024-01-01T00:00:00Z",
                "user": {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "avatar_url": "https://example.com/avatar.jpg"
                },
                "gig_job": {
                    "id": 1,
                    "title": "Web Development Project",
                    "description": "Build a modern website",
                    "min_salary": 1000.0,
                    "max_salary": 2000.0
                },
                "full_time_job": None
            }
        }
    
    @classmethod
    def from_orm(cls, obj, db_session=None, current_user_id=None):
        """Custom from_orm method to include relationships"""
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "gig_job_id": obj.gig_job_id,
            "full_time_job_id": obj.full_time_job_id,
            "created_at": obj.created_at,
            "user": None,
            "gig_job": None,
            "full_time_job": None
        }
        
        # Include user details if available
        if hasattr(obj, 'user') and obj.user:
            data["user"] = UserFullResponse.model_validate(obj.user)
        
        # Include gig job details if available
        if hasattr(obj, 'gig_job') and obj.gig_job and db_session:
            from ..repositories.gig_job_repository import GigJobRepository
            gig_repo = GigJobRepository(db_session)
            gig_data = gig_repo._prepare_gig_job_response(obj.gig_job, current_user_id)
            data["gig_job"] = gig_data
        
        # Include full-time job details if available
        if hasattr(obj, 'full_time_job') and obj.full_time_job and db_session:
            from ..repositories.full_time_job_repository import FullTimeJobRepository
            ft_repo = FullTimeJobRepository(db_session)
            ft_data = ft_repo._prepare_full_time_job_response(obj.full_time_job, current_user_id)
            data["full_time_job"] = ft_data
        
        return cls(**data)


class SavedJobListResponse(BaseModel):
    """Schema for paginated saved jobs list response"""
    items: list[SavedJobResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "gig_job_id": 1,
                        "full_time_job_id": None,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
        }


class SavedJobDetailedListResponse(BaseModel):
    """Schema for paginated saved jobs list response with full details"""
    items: list[SavedJobDetailedResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "gig_job_id": 1,
                        "full_time_job_id": None,
                        "created_at": "2024-01-01T00:00:00Z",
                        "user": {
                            "id": 1,
                            "name": "John Doe",
                            "email": "john@example.com"
                        },
                        "gig_job": {
                            "id": 1,
                            "title": "Web Development Project",
                            "description": "Build a modern website"
                        },
                        "full_time_job": None
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
        }
