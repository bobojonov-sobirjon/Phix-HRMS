from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class TeamMemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class TeamMemberStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    
    corporate_profile_id = Column(Integer, ForeignKey("corporate_profiles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    role = Column(Enum(TeamMemberRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(Enum(TeamMemberStatus, values_callable=lambda x: [e.value for e in x]), default=TeamMemberStatus.PENDING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    corporate_profile = relationship("CorporateProfile", back_populates="team_members")
    user = relationship("User", foreign_keys=[user_id], back_populates="team_memberships")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    
    def __repr__(self):
        return f"<TeamMember(id={self.id}, user_id={self.user_id}, role='{self.role}', status='{self.status}')>"
