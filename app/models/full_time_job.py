from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class WorkMode(str, enum.Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"


class ExperienceLevel(str, enum.Enum):
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    DIRECTOR = "director"


class JobStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DRAFT = "draft"


class FullTimeJob(Base):
    __tablename__ = "full_time_jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Job details
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    responsibilities = Column(Text, nullable=True)  # JSON string for responsibilities list
    location = Column(String(100), nullable=False, default="Worldwide")
    job_type = Column(Enum(JobType), nullable=False, default=JobType.FULL_TIME)
    work_mode = Column(Enum(WorkMode), nullable=False, default=WorkMode.ON_SITE)
    experience_level = Column(Enum(ExperienceLevel), nullable=False)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.ACTIVE)
    
    # Foreign keys
    company_id = Column(Integer, ForeignKey("corporate_profiles.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("CorporateProfile", back_populates="full_time_jobs")
    proposals = relationship("Proposal", back_populates="full_time_job", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="full_time_job_skills", back_populates="full_time_jobs")
    
    def __repr__(self):
        return f"<FullTimeJob(id={self.id}, title='{self.title}', company_id={self.company_id})>"
