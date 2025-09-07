from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .location import Location


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "ENTRY_LEVEL"
    MID_LEVEL = "MID_LEVEL"
    JUNIOR = "JUNIOR"
    DIRECTOR = "DIRECTOR"


class GigJobStatus(str, Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    FREELANCE = "FREELANCE"
    INTERNSHIP = "INTERNSHIP"


class WorkMode(str, Enum):
    ON_SITE = "ON_SITE"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    FLEXIBLE_HOURS = "FLEXIBLE_HOURS"


class ProjectLength(str, Enum):
    LESS_THAN_ONE_MONTH = "less_than_one_month"
    ONE_TO_THREE_MONTHS = "one_to_three_months"
    THREE_TO_SIX_MONTHS = "three_to_six_months"
    MORE_THAN_SIX_MONTHS = "more_than_six_months"


class DatePosted(str, Enum):
    ANY_TIME = "any_time"
    PAST_24_HOURS = "past_24_hours"
    PAST_WEEK = "past_week"
    PAST_MONTH = "past_month"


class SortBy(str, Enum):
    MOST_RECENT = "most_recent"
    MOST_RELEVANT = "most_relevant"


# Base schema
class GigJobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    location_id: Optional[int] = Field(None, description="Location ID")
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    job_type: JobType = Field(..., description="Job type (full-time, part-time, freelance, internship)")
    work_mode: WorkMode = Field(..., description="Work mode (on-site, remote, hybrid, flexible hours)")
    remote_only: bool = Field(False, description="Remote only option")
    skill_names: List[str] = Field(..., description="List of required skill names")
    min_salary: float = Field(..., gt=0, description="Minimum salary")
    max_salary: float = Field(..., gt=0, description="Maximum salary")
    deadline_days: int = Field(..., gt=0, le=365, description="Deadline in days")
    category_id: int = Field(..., description="Main category ID")
    subcategory_id: Optional[int] = Field(None, description="Subcategory ID")


# Create schema
class GigJobCreate(GigJobBase):
    pass


# Update schema
class GigJobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    location_id: Optional[int] = None
    experience_level: Optional[ExperienceLevel] = None
    job_type: Optional[JobType] = None
    work_mode: Optional[WorkMode] = None
    remote_only: Optional[bool] = None
    skill_names: Optional[List[str]] = None
    min_salary: Optional[float] = Field(None, gt=0)
    max_salary: Optional[float] = Field(None, gt=0)
    deadline_days: Optional[int] = Field(None, gt=0, le=365)
    status: Optional[GigJobStatus] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None


# Response schema
class GigJobResponse(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    location_id: Optional[int] = None
    location: Optional[Location] = None
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    job_type: JobType = Field(..., description="Job type (full-time, part-time, freelance, internship)")
    work_mode: WorkMode = Field(..., description="Work mode (on-site, remote, hybrid, flexible hours)")
    remote_only: bool = Field(False, description="Remote only option")
    min_salary: float = Field(..., gt=0, description="Minimum salary")
    max_salary: float = Field(..., gt=0, description="Maximum salary")
    deadline_days: int = Field(..., gt=0, le=365, description="Deadline in days")
    status: GigJobStatus
    author_id: int
    category_id: int
    category_name: str
    man_category: Optional[dict] = None
    subcategory_id: Optional[int] = None
    subcategory_name: Optional[str] = None
    sub_category: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    skills: List[dict] = Field(default_factory=list, description="List of skills with details")
    proposal_count: int = Field(default=0, description="Number of proposals for this job")
    
    model_config = {
        "from_attributes": True
    }


# Filter schema for API requests
class GigJobFilter(BaseModel):
    status_filter: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    work_mode: Optional[WorkMode] = None
    remote_only: Optional[bool] = None
    min_salary: Optional[float] = Field(None, gt=0)
    max_salary: Optional[float] = Field(None, gt=0)
    location_id: Optional[int] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    project_length: Optional[ProjectLength] = None
    date_posted: Optional[DatePosted] = None
    sort_by: Optional[SortBy] = SortBy.MOST_RECENT


# List response schema
class GigJobListResponse(BaseModel):
    items: List[GigJobResponse]
    total: int
    page: int
    size: int
    pages: int
