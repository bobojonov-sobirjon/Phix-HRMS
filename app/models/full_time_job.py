from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
from .team_member import TeamMemberRole


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class WorkMode(str, enum.Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"


class ExperienceLevel(str, enum.Enum):
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    DIRECTOR = "director"


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class PayPeriod(str, enum.Enum):
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_WEEK = "per_week"
    PER_MONTH = "per_month"
    PER_YEAR = "per_year"


class FullTimeJob(Base):
    __tablename__ = "full_time_jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    responsibilities = Column(Text, nullable=True)
    location = Column(String(100), nullable=False, default="Worldwide")
    job_type = Column(Enum(JobType, values_callable=lambda x: [e.value for e in x]), nullable=False, default=JobType.FULL_TIME)
    work_mode = Column(Enum(WorkMode, values_callable=lambda x: [e.value for e in x]), nullable=False, default=WorkMode.ON_SITE)
    experience_level = Column(Enum(ExperienceLevel, values_callable=lambda x: [e.value for e in x]), nullable=False)
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    pay_period = Column(Enum(PayPeriod, values_callable=lambda x: [e.value for e in x]), nullable=False, default=PayPeriod.PER_MONTH)
    status = Column(Enum(JobStatus, values_callable=lambda x: [e.value for e in x]), default=JobStatus.ACTIVE)
    
    company_id = Column(Integer, ForeignKey("corporate_profiles.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_role = Column(Enum(TeamMemberRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship("CorporateProfile", back_populates="full_time_jobs")
    category = relationship("Category", foreign_keys=[category_id], back_populates="full_time_jobs")
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    proposals = relationship("Proposal", back_populates="full_time_job", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="full_time_job_skills", back_populates="full_time_jobs")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    saved_jobs = relationship("SavedJob", back_populates="full_time_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FullTimeJob(id={self.id}, title='{self.title}', company_id={self.company_id})>"
