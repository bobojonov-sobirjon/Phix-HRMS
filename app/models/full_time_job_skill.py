from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class FullTimeJobSkill(Base):
    __tablename__ = "full_time_job_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    full_time_job_id = Column(Integer, ForeignKey("full_time_jobs.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<FullTimeJobSkill(full_time_job_id={self.full_time_job_id}, skill_id={self.skill_id})>"
