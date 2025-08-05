from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .job_post_type import JobPostType
from .location import Location

class JobBase(BaseModel):
    title: str
    description: Optional[str] = None
    job_post_type_id: int
    location_id: Optional[int] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    deadline: Optional[str] = None
    attachments: Optional[str] = None
    skill_names: Optional[List[str]] = None

class JobCreate(JobBase):
    user_id: int

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    job_post_type_id: Optional[int] = None
    location_id: Optional[int] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    deadline: Optional[str] = None
    attachments: Optional[str] = None
    skill_names: Optional[List[str]] = None

class Job(JobBase):
    id: int
    user_id: int
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    job_post_type: Optional[JobPostType] = None
    location: Optional[Location] = None
    
    class Config:
        from_attributes = True

class JobFilter(BaseModel):
    job_name: Optional[str] = None
    location_ids: Optional[List[int]] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None
    job_type: Optional[str] = None
    skip: int = 0
    limit: int = 100 