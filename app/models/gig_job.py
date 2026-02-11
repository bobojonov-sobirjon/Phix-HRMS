from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
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


class ProjectLength(str, enum.Enum):
    LESS_THAN_ONE_MONTH = "less_than_one_month"
    ONE_TO_THREE_MONTHS = "one_to_three_months"
    THREE_TO_SIX_MONTHS = "three_to_six_months"
    MORE_THAN_SIX_MONTHS = "more_than_six_months"


class GigJob(Base):
    __tablename__ = "gig_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    experience_level = Column(Enum(ExperienceLevel, values_callable=lambda x: [e.value for e in x]), nullable=False)
    project_length = Column(Enum(ProjectLength, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ProjectLength.LESS_THAN_ONE_MONTH)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    status = Column(Enum(GigJobStatus, values_callable=lambda x: [e.value for e in x]), default=GigJobStatus.ACTIVE)
    
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    author = relationship("User", back_populates="gig_jobs")
    category = relationship("Category", foreign_keys=[category_id], back_populates="gig_jobs")
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    location = relationship("Location")
    proposals = relationship("Proposal", back_populates="gig_job", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="gig_job_skills", back_populates="gig_jobs")
    saved_jobs = relationship("SavedJob", back_populates="gig_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GigJob(id={self.id}, title='{self.title}', author_id={self.author_id})>"
