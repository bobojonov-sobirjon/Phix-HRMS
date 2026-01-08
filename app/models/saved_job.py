from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gig_job_id = Column(Integer, ForeignKey("gig_jobs.id"), nullable=True)
    full_time_job_id = Column(Integer, ForeignKey("full_time_jobs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saved_jobs")
    gig_job = relationship("GigJob", back_populates="saved_jobs")
    full_time_job = relationship("FullTimeJob", back_populates="saved_jobs")

    def __repr__(self):
        return f"<SavedJob(id={self.id}, user_id={self.user_id}, gig_job_id={self.gig_job_id}, full_time_job_id={self.full_time_job_id})>"
