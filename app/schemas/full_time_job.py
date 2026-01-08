from pydantic import BaseModel, validator, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"


class WorkMode(str, Enum):
    ON_SITE = "ON_SITE"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "ENTRY_LEVEL"
    JUNIOR = "JUNIOR"
    MID_LEVEL = "MID_LEVEL"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    DIRECTOR = "DIRECTOR"


class JobStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"


class PayPeriod(str, Enum):
    PER_HOUR = "PER_HOUR"
    PER_DAY = "PER_DAY"
    PER_WEEK = "PER_WEEK"
    PER_MONTH = "PER_MONTH"
    PER_YEAR = "PER_YEAR"


class FullTimeJobBase(BaseModel):
    title: str
    description: str
    responsibilities: Optional[str] = None
    location: str = "Worldwide"
    job_type: JobType = JobType.FULL_TIME
    work_mode: WorkMode = WorkMode.ON_SITE
    experience_level: ExperienceLevel
    skill_ids: List[int] = Field(..., description="List of skill IDs")
    min_salary: float
    max_salary: float
    pay_period: PayPeriod = PayPeriod.PER_MONTH
    status: JobStatus = JobStatus.ACTIVE
    category_id: int = Field(..., description="Main category ID")
    subcategory_id: Optional[int] = Field(None, description="Subcategory ID")
    corporate_profile_id: int = Field(..., description="Corporate profile ID")


class FullTimeJobCreate(FullTimeJobBase):
    pass


class FullTimeJobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    work_mode: Optional[WorkMode] = None
    experience_level: Optional[ExperienceLevel] = None
    skill_ids: Optional[List[int]] = Field(None, description="List of skill IDs")
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    pay_period: Optional[PayPeriod] = None
    status: Optional[JobStatus] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None


class FullTimeJobResponse(BaseModel):
    id: int
    title: str
    description: str
    responsibilities: Optional[str] = None
    location: str = "Worldwide"
    job_type: str = "FULL_TIME"
    work_mode: str = "ON_SITE"
    experience_level: str
    min_salary: float
    max_salary: float
    pay_period: str = "PER_MONTH"
    status: str = "ACTIVE"
    company_id: int
    company_name: str
    company_logo_url: Optional[str] = Field(None, description="Company logo URL")
    category_id: int
    category_name: str
    subcategory_id: Optional[int] = None
    subcategory_name: Optional[str] = None
    created_by_user_id: int
    created_by_user_name: str
    created_by_role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    skills: List[dict] = Field(default_factory=list, description="List of skills with details")
    all_jobs_count: int = Field(default=0, description="Total number of jobs created by the user")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score (only when token is provided)")
    is_saved: bool = Field(default=False, description="Whether the job is saved by the current user")
    is_send_proposal: bool = Field(default=False, description="Whether the current user has sent a proposal for this job")
    company_followers_count: int = Field(default=0, description="Number of followers for the company")
    company_follow_relation_id: Optional[int] = Field(default=None, description="ID of the follow relationship if current user is following the company")
    
    class Config:
        from_attributes = True


class FullTimeJobListResponse(BaseModel):
    jobs: List[FullTimeJobResponse]
    total: int
    page: int
    size: int


class UserFullTimeJobsResponse(BaseModel):
    user_jobs: List[FullTimeJobResponse]
    total: int
    page: int
    size: int
