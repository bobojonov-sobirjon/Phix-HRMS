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
    ACTIVE = "ACTIVE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProjectLength(str, Enum):
    LESS_THAN_ONE_MONTH = "LESS_THAN_ONE_MONTH"
    ONE_TO_THREE_MONTHS = "ONE_TO_THREE_MONTHS"
    THREE_TO_SIX_MONTHS = "THREE_TO_SIX_MONTHS"
    MORE_THAN_SIX_MONTHS = "MORE_THAN_SIX_MONTHS"


class DatePosted(str, Enum):
    ANY_TIME = "ANY_TIME"
    PAST_24_HOURS = "PAST_24_HOURS"
    PAST_WEEK = "PAST_WEEK"
    PAST_MONTH = "PAST_MONTH"


class SortBy(str, Enum):
    MOST_RECENT = "MOST_RECENT"
    MOST_RELEVANT = "MOST_RELEVANT"


# Base schema
class GigJobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    project_length: ProjectLength = Field(..., description="Project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)")
    skill_ids: List[int] = Field(..., description="List of required skill IDs")
    min_salary: float = Field(..., gt=0, description="Minimum salary")
    max_salary: float = Field(..., gt=0, description="Maximum salary")
    category_id: int = Field(..., description="Main category ID")
    subcategory_id: Optional[int] = Field(None, description="Subcategory ID")
    location_id: Optional[int] = Field(None, description="Location ID")


# Create schema
class GigJobCreate(GigJobBase):
    pass


# Update schema
class GigJobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    experience_level: Optional[ExperienceLevel] = None
    project_length: Optional[ProjectLength] = None
    skill_ids: Optional[List[int]] = None
    min_salary: Optional[float] = Field(None, gt=0)
    max_salary: Optional[float] = Field(None, gt=0)
    status: Optional[GigJobStatus] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    location_id: Optional[int] = None


# Response schema
class GigJobResponse(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    location: Optional[Location] = None
    experience_level: str = Field(..., description="Required experience level")
    project_length: str = Field(..., description="Project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)")
    min_salary: float = Field(..., gt=0, description="Minimum salary")
    max_salary: float = Field(..., gt=0, description="Maximum salary")
    status: str
    author: Optional[dict] = None
    man_category: Optional[dict] = None
    sub_category: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    skills: List[dict] = Field(default_factory=list, description="List of skills with details")
    proposal_count: int = Field(default=0, description="Number of proposals for this job")
    all_jobs_count: int = Field(default=0, description="Total number of jobs created by the author")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score (only when token is provided)")
    
    model_config = {
        "from_attributes": True
    }


# Filter schema for API requests
class GigJobFilter(BaseModel):
    status_filter: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = None
    project_length: Optional[ProjectLength] = None
    min_salary: Optional[float] = Field(None, gt=0)
    max_salary: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    date_posted: Optional[DatePosted] = None
    sort_by: Optional[SortBy] = SortBy.MOST_RECENT


# GigJobSkill removal schema
class GigJobSkillRemove(BaseModel):
    gig_job_skill_id: int = Field(..., description="GigJobSkill ID to remove from the gig job")

# List response schema
class GigJobListResponse(BaseModel):
    items: List[GigJobResponse]
    total: int
    page: int
    size: int
    pages: int
