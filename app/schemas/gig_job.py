from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "entry_level"
    MID_LEVEL = "mid_level"
    JUNIOR = "junior"
    DIRECTOR = "director"


class GigJobStatus(str, Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class WorkMode(str, Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE_HOURS = "flexible_hours"


# Base schema
class GigJobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    location: str = Field(..., max_length=100, description="Job location")
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    job_type: JobType = Field(..., description="Job type (full-time, part-time, freelance, internship)")
    work_mode: WorkMode = Field(..., description="Work mode (on-site, remote, hybrid, flexible hours)")
    remote_only: bool = Field(False, description="Remote only option")
    skill_names: List[str] = Field(..., description="List of required skill names")
    min_salary: float = Field(..., gt=0, description="Minimum salary")
    max_salary: float = Field(..., gt=0, description="Maximum salary")
    deadline_days: int = Field(..., gt=0, le=365, description="Deadline in days")


# Create schema
class GigJobCreate(GigJobBase):
    pass


# Update schema
class GigJobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    location: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[ExperienceLevel] = None
    job_type: Optional[JobType] = None
    work_mode: Optional[WorkMode] = None
    remote_only: Optional[bool] = None
    skill_names: Optional[List[str]] = None
    min_salary: Optional[float] = Field(None, gt=0)
    max_salary: Optional[float] = Field(None, gt=0)
    deadline_days: Optional[int] = Field(None, gt=0, le=365)
    status: Optional[GigJobStatus] = None


# Response schema
class GigJobResponse(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    location: str = Field(..., max_length=100, description="Job location")
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    job_type: JobType = Field(..., description="Job type (full-time, part-time, freelance, internship)")
    work_mode: WorkMode = Field(..., description="Work mode (on-site, remote, hybrid, flexible hours)")
    remote_only: bool = Field(False, description="Remote only option")
    min_salary: float = Field(..., gt=0, description="Minimum salary")
    max_salary: float = Field(..., gt=0, description="Maximum salary")
    deadline_days: int = Field(..., gt=0, le=365, description="Deadline in days")
    status: GigJobStatus
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    skills: List[dict] = Field(default_factory=list, description="List of skills with details")
    
    model_config = {
        "from_attributes": True
    }


# List response schema
class GigJobListResponse(BaseModel):
    items: List[GigJobResponse]
    total: int
    page: int
    size: int
    pages: int
