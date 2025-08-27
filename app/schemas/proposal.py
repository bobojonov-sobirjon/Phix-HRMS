from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Base schema
class ProposalBase(BaseModel):
    cover_letter: str = Field(..., min_length=10, description="Cover letter content")
    attachments: Optional[str] = Field(None, description="File attachments (JSON string)")


# Create schema
class ProposalCreate(ProposalBase):
    gig_job_id: Optional[int] = Field(None, description="ID of the gig job (for gig jobs)")
    full_time_job_id: Optional[int] = Field(None, description="ID of the full-time job (for full-time jobs)")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.gig_job_id and not self.full_time_job_id:
            raise ValueError("Either gig_job_id or full_time_job_id must be provided")
        if self.gig_job_id and self.full_time_job_id:
            raise ValueError("Only one of gig_job_id or full_time_job_id can be provided")


# Update schema
class ProposalUpdate(BaseModel):
    cover_letter: Optional[str] = Field(None, min_length=10)
    attachments: Optional[str] = None


# Response schema
class ProposalResponse(ProposalBase):
    id: int
    user_id: int
    gig_job_id: Optional[int] = None
    full_time_job_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


# List response schema
class ProposalListResponse(BaseModel):
    items: List[ProposalResponse]
    total: int
    page: int
    size: int
    pages: int
