from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from fastapi import UploadFile
from app.core.config import settings
from .gig_job import GigJobResponse
from .full_time_job import FullTimeJobResponse
from .profile import UserFullResponse, UserShortDetails


class ProposalAttachmentBase(BaseModel):
    attachment: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    name: str = Field(..., description="Original file name")


class ProposalAttachmentResponse(ProposalAttachmentBase):
    id: int
    proposal_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


class ProposalBase(BaseModel):
    cover_letter: str = Field(..., min_length=10, description="Cover letter content")
    delivery_time: Optional[int] = Field(None, ge=1, description="Delivery time in days")
    offer_amount: Optional[float] = Field(None, ge=0, description="Offer amount in currency")


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


class ProposalCreate(ProposalBase):
    gig_job_id: Optional[int] = Field(None, description="ID of the gig job (for gig jobs)")
    full_time_job_id: Optional[int] = Field(None, description="ID of the full-time job (for full-time jobs)")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.gig_job_id and not self.full_time_job_id:
            raise ValueError("Either gig_job_id or full_time_job_id must be provided")
        if self.gig_job_id and self.full_time_job_id:
            raise ValueError("Only one of gig_job_id or full_time_job_id can be provided")


class ProposalUpdateForm(BaseModel):
    cover_letter: Optional[str] = Field(None, min_length=10)
    delivery_time: Optional[int] = Field(None, ge=1)
    offer_amount: Optional[float] = Field(None, ge=0)
    attachments: Optional[List[UploadFile]] = None


class ProposalUpdate(BaseModel):
    cover_letter: Optional[str] = Field(None, min_length=10)
    delivery_time: Optional[int] = Field(None, ge=1)
    offer_amount: Optional[float] = Field(None, ge=0)


class ProposalResponse(ProposalBase):
    id: int
    user_id: int
    gig_job_id: Optional[int] = None
    full_time_job_id: Optional[int] = None
    is_read: bool = Field(default=False, description="Whether the proposal has been read by the job owner")
    attachments: Optional[List[ProposalAttachmentResponse]] = Field(None, description="File attachments")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    user: Optional[UserShortDetails] = None
    gig_job: Optional[GigJobResponse] = None
    full_time_job: Optional[FullTimeJobResponse] = None
    
    model_config = {
        "from_attributes": True
    }
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to include relationships and attachments"""
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "gig_job_id": obj.gig_job_id,
            "full_time_job_id": obj.full_time_job_id,
            "cover_letter": obj.cover_letter,
            "delivery_time": obj.delivery_time,
            "offer_amount": obj.offer_amount,
            "is_read": getattr(obj, 'is_read', False),
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "attachments": [],
            "user": None,
            "gig_job": None,
            "full_time_job": None
        }
        
        if hasattr(obj, 'attachments') and obj.attachments:
            attachment_list = []
            for attachment in obj.attachments:
                attachment_url = attachment.attachment
                if attachment_url and not attachment_url.startswith(('http://', 'https://')):
                    attachment_url = f"{settings.BASE_URL}/static/{attachment_url}"
                
                attachment_dict = {
                    "id": attachment.id,
                    "proposal_id": attachment.proposal_id,
                    "attachment": attachment_url,
                    "size": attachment.size,
                    "name": attachment.name,
                    "created_at": attachment.created_at,
                    "updated_at": attachment.updated_at
                }
                attachment_list.append(ProposalAttachmentResponse(**attachment_dict))
            data["attachments"] = attachment_list
        
        if hasattr(obj, 'user') and obj.user:
            data["user"] = UserShortDetails.model_validate(obj.user)
        
        if hasattr(obj, 'gig_job') and obj.gig_job:
            data["gig_job"] = cls._prepare_gig_job_data(obj.gig_job)
        
        if hasattr(obj, 'full_time_job') and obj.full_time_job:
            data["full_time_job"] = cls._prepare_full_time_job_data(obj.full_time_job)
        
        return cls(**data)
    
    @classmethod
    def _prepare_gig_job_data(cls, gig_job):
        """Prepare gig job data for response"""
        if not gig_job:
            return None
        
        if isinstance(gig_job, dict):
            return gig_job
            
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
        
        location_data = None
        if hasattr(gig_job, 'location') and gig_job.location:
            location_data = {
                "id": gig_job.location.id,
                "name": gig_job.location.name,
                "flag_image": f"{settings.BASE_URL}{gig_job.location.flag_image}" if gig_job.location.flag_image and not gig_job.location.flag_image.startswith(('http://', 'https://')) else gig_job.location.flag_image,
                "code": gig_job.location.code,
                "phone_code": gig_job.location.phone_code,
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
            "experience_level": cls._normalize_enum_value(gig_job.experience_level, 'ExperienceLevel'),
            "project_length": gig_job.project_length,
            "min_salary": gig_job.min_salary,
            "max_salary": gig_job.max_salary,
            "status": cls._normalize_enum_value(gig_job.status, 'GigJobStatus'),
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
        
        if isinstance(full_time_job, dict):
            return full_time_job
            
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
        
        category_name = 'Unknown Category'
        if hasattr(full_time_job, 'category') and full_time_job.category:
            category_name = full_time_job.category.name
        
        subcategory_name = None
        if hasattr(full_time_job, 'subcategory') and full_time_job.subcategory:
            subcategory_name = full_time_job.subcategory.name
        
        company_name = 'Unknown Company'
        if hasattr(full_time_job, 'company') and full_time_job.company:
            company_name = full_time_job.company.company_name
        
        created_by_user_name = 'Unknown User'
        created_by_user_id = 0
        if hasattr(full_time_job, 'created_by_user') and full_time_job.created_by_user:
            created_by_user_name = full_time_job.created_by_user.name
            created_by_user_id = full_time_job.created_by_user.id
        
        created_by_role = 'UNKNOWN'
        if hasattr(full_time_job, 'created_by_role') and full_time_job.created_by_role:
            if hasattr(full_time_job.created_by_role, 'value'):
                created_by_role = full_time_job.created_by_role.value
            else:
                created_by_role = str(full_time_job.created_by_role)
        
        return {
            "id": full_time_job.id,
            "title": full_time_job.title,
            "description": full_time_job.description,
            "responsibilities": full_time_job.responsibilities,
            "location": full_time_job.location,
            "job_type": cls._normalize_enum_value(full_time_job.job_type, 'JobType'),
            "work_mode": cls._normalize_enum_value(full_time_job.work_mode, 'WorkMode'),
            "experience_level": cls._normalize_enum_value(full_time_job.experience_level, 'ExperienceLevel'),
            "min_salary": full_time_job.min_salary,
            "max_salary": full_time_job.max_salary,
            "pay_period": cls._normalize_enum_value(getattr(full_time_job, 'pay_period', None), 'PayPeriod') or "PER_MONTH",
            "status": cls._normalize_enum_value(full_time_job.status, 'JobStatus'),
            "company_id": full_time_job.company_id,
            "company_name": company_name,
            "category_id": full_time_job.category_id,
            "category_name": category_name,
            "subcategory_id": full_time_job.subcategory_id,
            "subcategory_name": subcategory_name,
            "created_by_user_id": created_by_user_id if created_by_user_id else full_time_job.created_by_user_id,
            "created_by_user_name": created_by_user_name,
            "created_by_role": created_by_role,
            "created_at": full_time_job.created_at,
            "updated_at": full_time_job.updated_at,
            "skills": skills_data,
            "all_jobs_count": 0,
            "relevance_score": None,
            "is_saved": False,
            "is_send_proposal": False,
            "company_followers_count": 0,
            "company_follow_relation_id": None
        }
    
    @classmethod
    def _normalize_enum_value(cls, value, enum_type):
        """Normalize enum values to uppercase for Pydantic validation"""
        if hasattr(value, 'value'):
            return value.value
        elif isinstance(value, str):
            return value.upper()
        else:
            return str(value).upper()


class ProposalListResponse(BaseModel):
    items: List[ProposalResponse]
    total: int
    page: int
    size: int
    pages: int
