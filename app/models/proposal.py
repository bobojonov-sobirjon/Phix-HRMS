from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    cover_letter = Column(Text, nullable=False)
    attachments = Column(Text, nullable=True)  # JSON string for file paths
    
    # Foreign keys - one of these must be set
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gig_job_id = Column(Integer, ForeignKey("gig_jobs.id"), nullable=True)  # For gig jobs
    full_time_job_id = Column(Integer, ForeignKey("full_time_jobs.id"), nullable=True)  # For full-time jobs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="proposals")
    gig_job = relationship("GigJob", back_populates="proposals")
    full_time_job = relationship("FullTimeJob", back_populates="proposals")
    
    def __repr__(self):
        return f"<Proposal(id={self.id}, user_id={self.user_id}, gig_job_id={self.gig_job_id}, full_time_job_id={self.full_time_job_id})>"
