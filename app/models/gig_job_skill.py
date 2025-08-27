from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class GigJobSkill(Base):
    __tablename__ = "gig_job_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    gig_job_id = Column(Integer, ForeignKey("gig_jobs.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<GigJobSkill(gig_job_id={self.gig_job_id}, skill_id={self.skill_id})>"
