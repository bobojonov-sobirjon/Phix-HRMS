from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class WorkMode(str, Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    DIRECTOR = "director"


class JobStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DRAFT = "draft"


# Base schema
class FullTimeJobBase(BaseModel):
    title: str
    description: str
    responsibilities: Optional[str] = None  # JSON string for responsibilities list
    location: str = "Worldwide"
    job_type: JobType = JobType.FULL_TIME
    work_mode: WorkMode = WorkMode.ON_SITE
    experience_level: ExperienceLevel
    skill_names: List[str]  # List of skill names
    min_salary: float
    max_salary: float
    status: JobStatus = JobStatus.ACTIVE
    category_id: int = Field(..., description="Main category ID")
    subcategory_id: Optional[int] = Field(None, description="Subcategory ID")


# Create schema
class FullTimeJobCreate(FullTimeJobBase):
    pass


# Update schema
class FullTimeJobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    work_mode: Optional[WorkMode] = None
    experience_level: Optional[ExperienceLevel] = None
    skill_names: Optional[List[str]] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    status: Optional[JobStatus] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None


# Response schema
class FullTimeJobResponse(BaseModel):
    id: int
    title: str
    description: str
    responsibilities: Optional[str] = None
    location: str = "Worldwide"
    job_type: JobType = JobType.FULL_TIME
    work_mode: WorkMode = WorkMode.ON_SITE
    experience_level: ExperienceLevel
    min_salary: float
    max_salary: float
    status: JobStatus = JobStatus.ACTIVE
    company_id: int
    company_name: str
    category_id: int
    category_name: str
    subcategory_id: Optional[int] = None
    subcategory_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    skills: List[dict] = Field(default_factory=list, description="List of skills with details")
    
    class Config:
        from_attributes = True


# List response schema
class FullTimeJobListResponse(BaseModel):
    jobs: List[FullTimeJobResponse]
    total: int
    page: int
    size: int


# User jobs response schema
class UserFullTimeJobsResponse(BaseModel):
    user_jobs: List[FullTimeJobResponse]
    total: int
    page: int
    size: int
