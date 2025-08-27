from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ExperienceLevel(str, enum.Enum):
    ENTRY_LEVEL = "entry_level"
    MID_LEVEL = "mid_level"
    JUNIOR = "junior"
    DIRECTOR = "director"


class GigJobStatus(str, enum.Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class WorkMode(str, enum.Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE_HOURS = "flexible_hours"


class GigJob(Base):
    __tablename__ = "gig_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String(100), nullable=False, default="Worldwide")
    experience_level = Column(Enum(ExperienceLevel), nullable=False)
    job_type = Column(Enum(JobType), nullable=False, default=JobType.FREELANCE)
    work_mode = Column(Enum(WorkMode), nullable=False, default=WorkMode.REMOTE)
    remote_only = Column(Boolean, default=False)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    deadline_days = Column(Integer, nullable=False, default=7)
    status = Column(Enum(GigJobStatus), default=GigJobStatus.ACTIVE)
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="gig_jobs")
    proposals = relationship("Proposal", back_populates="gig_job", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="gig_job_skills", back_populates="gig_jobs")
    
    def __repr__(self):
        return f"<GigJob(id={self.id}, title='{self.title}', author_id={self.author_id})>"
