from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic job information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_post_type_id = Column(Integer, ForeignKey('job_post_types.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    
    # Job details
    experience_level = Column(String(100), nullable=True)  # Junior, Senior, etc.
    work_mode = Column(String(100), nullable=True)  # Remote, On-site, Hybrid
    job_type = Column(String(100), nullable=True)  # Full-time, Part-time, Contract
    
    # Salary information
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    
    # Additional fields
    deadline = Column(String(100), nullable=True)  # 7 Days, 30 Days, etc.
    attachments = Column(Text, nullable=True)  # File paths or URLs
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship('User', back_populates='jobs')
    job_post_type = relationship('JobPostType', back_populates='jobs')
    location = relationship('Location')
    skills = relationship('Skill', secondary='job_skills', back_populates='jobs') 