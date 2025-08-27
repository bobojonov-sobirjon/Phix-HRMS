from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    users = relationship('User', secondary='user_skills', back_populates='skills', viewonly=True)
    gig_jobs = relationship('GigJob', secondary='gig_job_skills', back_populates='skills', viewonly=True)
    full_time_jobs = relationship('FullTimeJob', secondary='full_time_job_skills', back_populates='skills', viewonly=True) 