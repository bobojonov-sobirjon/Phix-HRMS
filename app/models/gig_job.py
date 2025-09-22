from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ExperienceLevel(str, enum.Enum):
    ENTRY_LEVEL = "ENTRY_LEVEL"
    MID_LEVEL = "MID_LEVEL"
    JUNIOR = "JUNIOR"
    DIRECTOR = "DIRECTOR"


class GigJobStatus(str, enum.Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectLength(str, enum.Enum):
    LESS_THAN_ONE_MONTH = "LESS_THAN_ONE_MONTH"
    ONE_TO_THREE_MONTHS = "ONE_TO_THREE_MONTHS"
    THREE_TO_SIX_MONTHS = "THREE_TO_SIX_MONTHS"
    MORE_THAN_SIX_MONTHS = "MORE_THAN_SIX_MONTHS"


class GigJob(Base):
    __tablename__ = "gig_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    experience_level = Column(Enum(ExperienceLevel), nullable=False)
    project_length = Column(Enum(ProjectLength), nullable=False, default=ProjectLength.LESS_THAN_ONE_MONTH)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    status = Column(Enum(GigJobStatus), default=GigJobStatus.ACTIVE)
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    author = relationship("User", back_populates="gig_jobs")
    category = relationship("Category", foreign_keys=[category_id], back_populates="gig_jobs")
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    location = relationship("Location")
    proposals = relationship("Proposal", back_populates="gig_job", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="gig_job_skills", back_populates="gig_jobs")
    
    def __repr__(self):
        return f"<GigJob(id={self.id}, title='{self.title}', author_id={self.author_id})>"
