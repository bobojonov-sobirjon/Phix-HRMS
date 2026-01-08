from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class CorporateProfileFollow(Base):
    __tablename__ = "corporate_profile_follows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    corporate_profile_id = Column(Integer, ForeignKey("corporate_profiles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="corporate_profile_follows")
    corporate_profile = relationship("CorporateProfile", back_populates="followers")

    __table_args__ = (
        UniqueConstraint('user_id', 'corporate_profile_id', name='uq_user_corporate_profile_follow'),
    )

    def __repr__(self):
        return f"<CorporateProfileFollow(id={self.id}, user_id={self.user_id}, corporate_profile_id={self.corporate_profile_id})>"

