from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from .team_member import TeamMemberRole


class JobType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"


class WorkMode(str, enum.Enum):
    ON_SITE = "ON_SITE"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"


class ExperienceLevel(str, enum.Enum):
    ENTRY_LEVEL = "ENTRY_LEVEL"
    JUNIOR = "JUNIOR"
    MID_LEVEL = "MID_LEVEL"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    DIRECTOR = "DIRECTOR"


class JobStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"


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
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Job creation context
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_role = Column(Enum(TeamMemberRole), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("CorporateProfile", back_populates="full_time_jobs")
    category = relationship("Category", foreign_keys=[category_id], back_populates="full_time_jobs")
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    proposals = relationship("Proposal", back_populates="full_time_job", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="full_time_job_skills", back_populates="full_time_jobs")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self):
        return f"<FullTimeJob(id={self.id}, title='{self.title}', company_id={self.company_id})>"
