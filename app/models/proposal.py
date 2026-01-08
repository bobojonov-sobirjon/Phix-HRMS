from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    cover_letter = Column(Text, nullable=False)
    delivery_time = Column(Integer, nullable=True)
    offer_amount = Column(Float, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gig_job_id = Column(Integer, ForeignKey("gig_jobs.id"), nullable=True)
    full_time_job_id = Column(Integer, ForeignKey("full_time_jobs.id"), nullable=True)
    
    is_read = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="proposals")
    gig_job = relationship("GigJob", back_populates="proposals")
    full_time_job = relationship("FullTimeJob", back_populates="proposals")
    attachments = relationship("ProposalAttachment", back_populates="proposal")
    notifications = relationship("Notification", back_populates="proposal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Proposal(id={self.id}, user_id={self.user_id}, gig_job_id={self.gig_job_id}, full_time_job_id={self.full_time_job_id})>"
