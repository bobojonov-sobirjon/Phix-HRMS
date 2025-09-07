from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from fastapi import UploadFile
from app.config import settings
from .gig_job import GigJobResponse
from .full_time_job import FullTimeJobResponse
from .profile import UserFullResponse


# Base schema
class ProposalBase(BaseModel):
    cover_letter: str = Field(..., min_length=10, description="Cover letter content")
    delivery_time: Optional[int] = Field(None, ge=1, description="Delivery time in days")
    offer_amount: Optional[float] = Field(None, ge=0, description="Offer amount in currency")


# Create schema for form data
class ProposalCreateForm(BaseModel):
    cover_letter: str = Field(..., min_length=10, description="Cover letter content")
    delivery_time: Optional[int] = Field(None, ge=1, description="Delivery time in days")
    offer_amount: Optional[float] = Field(None, ge=0, description="Offer amount in currency")
    gig_job_id: Optional[int] = Field(None, description="ID of the gig job (for gig jobs)")
    full_time_job_id: Optional[int] = Field(None, description="ID of the full-time job (for full-time jobs)")
    attachments: Optional[List[UploadFile]] = Field(None, description="File attachments")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.gig_job_id and not self.full_time_job_id:
            raise ValueError("Either gig_job_id or full_time_job_id must be provided")
        if self.gig_job_id and self.full_time_job_id:
            raise ValueError("Only one of gig_job_id or full_time_job_id can be provided")


# Create schema (for backward compatibility)
class ProposalCreate(ProposalBase):
    attachments: Optional[str] = Field(None, description="File attachments (JSON string)")
    gig_job_id: Optional[int] = Field(None, description="ID of the gig job (for gig jobs)")
    full_time_job_id: Optional[int] = Field(None, description="ID of the full-time job (for full-time jobs)")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.gig_job_id and not self.full_time_job_id:
            raise ValueError("Either gig_job_id or full_time_job_id must be provided")
        if self.gig_job_id and self.full_time_job_id:
            raise ValueError("Only one of gig_job_id or full_time_job_id can be provided")


# Update schema for form data
class ProposalUpdateForm(BaseModel):
    cover_letter: Optional[str] = Field(None, min_length=10)
    delivery_time: Optional[int] = Field(None, ge=1)
    offer_amount: Optional[float] = Field(None, ge=0)
    attachments: Optional[List[UploadFile]] = None


# Update schema (for backward compatibility)
class ProposalUpdate(BaseModel):
    cover_letter: Optional[str] = Field(None, min_length=10)
    delivery_time: Optional[int] = Field(None, ge=1)
    offer_amount: Optional[float] = Field(None, ge=0)
    attachments: Optional[str] = None


# Response schema
class ProposalResponse(ProposalBase):
    id: int
    user_id: int
    gig_job_id: Optional[int] = None
    full_time_job_id: Optional[int] = None
    attachments: Optional[List[str]] = Field(None, description="File attachments (array of file paths)")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Full details
    user: Optional[UserFullResponse] = None
    gig_job: Optional[GigJobResponse] = None
    full_time_job: Optional[FullTimeJobResponse] = None
    
    model_config = {
        "from_attributes": True
    }
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to parse attachments JSON string and include relationships"""
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "gig_job_id": obj.gig_job_id,
            "full_time_job_id": obj.full_time_job_id,
            "cover_letter": obj.cover_letter,
            "delivery_time": obj.delivery_time,
            "offer_amount": obj.offer_amount,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "attachments": None,
            "user": None,
            "gig_job": None,
            "full_time_job": None
        }
        
        # Parse attachments JSON string to array
        if obj.attachments:
            import json
            try:
                # Handle double backslashes in the JSON string
                attachments_str = obj.attachments.replace('\\\\', '/')
                attachments = json.loads(attachments_str)
                # Add base URL to each attachment path
                data["attachments"] = [f"{settings.BASE_URL}/static/{attachment}" for attachment in attachments]
            except (json.JSONDecodeError, TypeError):
                data["attachments"] = []
        
        # Include user details if available
        if hasattr(obj, 'user') and obj.user:
            data["user"] = UserFullResponse.from_orm(obj.user)
        
        # Include gig job details if available
        if hasattr(obj, 'gig_job') and obj.gig_job:
            data["gig_job"] = cls._prepare_gig_job_data(obj.gig_job)
        
        # Include full-time job details if available
        if hasattr(obj, 'full_time_job') and obj.full_time_job:
            data["full_time_job"] = cls._prepare_full_time_job_data(obj.full_time_job)
        
        return cls(**data)
    
    @classmethod
    def _prepare_gig_job_data(cls, gig_job):
        """Prepare gig job data for response"""
        if not gig_job:
            return None
            
        # Convert skills to dict format
        skills_data = []
        if hasattr(gig_job, 'skills') and gig_job.skills:
            for skill in gig_job.skills:
                skills_data.append({
                    "id": skill.id,
                    "name": skill.name,
                    "created_at": skill.created_at,
                    "updated_at": skill.updated_at,
                    "is_deleted": getattr(skill, 'is_deleted', False)
                })
        
        # Prepare location data
        location_data = None
        if hasattr(gig_job, 'location') and gig_job.location:
            location_data = {
                "id": gig_job.location.id,
                "name": gig_job.location.name,
                "flag_image": f"{settings.BASE_URL}{gig_job.location.flag_image}" if gig_job.location.flag_image and not gig_job.location.flag_image.startswith(('http://', 'https://')) else gig_job.location.flag_image,
                "code": gig_job.location.code,
                "created_at": gig_job.location.created_at,
                "updated_at": gig_job.location.updated_at,
                "is_deleted": getattr(gig_job.location, 'is_deleted', False)
            }
        
        return {
            "id": gig_job.id,
            "title": gig_job.title,
            "description": gig_job.description,
            "location_id": gig_job.location_id,
            "location": location_data,
            "experience_level": gig_job.experience_level,
            "job_type": gig_job.job_type,
            "work_mode": gig_job.work_mode,
            "remote_only": gig_job.remote_only,
            "min_salary": gig_job.min_salary,
            "max_salary": gig_job.max_salary,
            "deadline_days": gig_job.deadline_days,
            "status": gig_job.status,
            "author_id": gig_job.author_id,
            "category_id": gig_job.category_id,
            "category_name": gig_job.category.name if hasattr(gig_job, 'category') and gig_job.category else None,
            "man_category": {
                "id": gig_job.category.id,
                "name": gig_job.category.name,
                "description": gig_job.category.description,
                "is_active": gig_job.category.is_active,
                "created_at": gig_job.category.created_at,
                "updated_at": gig_job.category.updated_at
            } if hasattr(gig_job, 'category') and gig_job.category else None,
            "subcategory_id": gig_job.subcategory_id,
            "subcategory_name": gig_job.subcategory.name if hasattr(gig_job, 'subcategory') and gig_job.subcategory else None,
            "sub_category": {
                "id": gig_job.subcategory.id,
                "name": gig_job.subcategory.name,
                "description": gig_job.subcategory.description,
                "is_active": gig_job.subcategory.is_active,
                "created_at": gig_job.subcategory.created_at,
                "updated_at": gig_job.subcategory.updated_at
            } if hasattr(gig_job, 'subcategory') and gig_job.subcategory else None,
            "created_at": gig_job.created_at,
            "updated_at": gig_job.updated_at,
            "skills": skills_data,
            "proposal_count": len(gig_job.proposals) if hasattr(gig_job, 'proposals') and gig_job.proposals else 0
        }
    
    @classmethod
    def _prepare_full_time_job_data(cls, full_time_job):
        """Prepare full-time job data for response"""
        if not full_time_job:
            return None
            
        # Convert skills to dict format
        skills_data = []
        if hasattr(full_time_job, 'skills') and full_time_job.skills:
            for skill in full_time_job.skills:
                skills_data.append({
                    "id": skill.id,
                    "name": skill.name,
                    "created_at": skill.created_at,
                    "updated_at": skill.updated_at,
                    "is_deleted": getattr(skill, 'is_deleted', False)
                })
        
        return {
            "id": full_time_job.id,
            "title": full_time_job.title,
            "description": full_time_job.description,
            "responsibilities": full_time_job.responsibilities,
            "location": full_time_job.location,
            "job_type": full_time_job.job_type,
            "work_mode": full_time_job.work_mode,
            "experience_level": full_time_job.experience_level,
            "min_salary": full_time_job.min_salary,
            "max_salary": full_time_job.max_salary,
            "status": full_time_job.status,
            "company_id": full_time_job.company_id,
            "company_name": getattr(full_time_job, 'company_name', 'Unknown Company'),
            "category_id": full_time_job.category_id,
            "category_name": getattr(full_time_job, 'category_name', 'Unknown Category'),
            "subcategory_id": full_time_job.subcategory_id,
            "subcategory_name": getattr(full_time_job, 'subcategory_name', None),
            "created_at": full_time_job.created_at,
            "updated_at": full_time_job.updated_at,
            "skills": skills_data
        }


# List response schema
class ProposalListResponse(BaseModel):
    items: List[ProposalResponse]
    total: int
    page: int
    size: int
    pages: int
