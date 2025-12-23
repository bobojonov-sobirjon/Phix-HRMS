from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class CompanySize(str, enum.Enum):
    STARTUP = "1-10"
    SMALL = "10-50"
    MEDIUM = "50-200"
    LARGE = "200-1000"
    ENTERPRISE = "1000+"


class CorporateProfile(Base):
    __tablename__ = "corporate_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Company information
    company_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    country_code = Column(String(10), nullable=False, default="+1")
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    overview = Column(Text, nullable=False)
    website_url = Column(String(255), nullable=True)
    company_size = Column(Enum(CompanySize), nullable=False)
    logo_url = Column(Text, nullable=True)

    # Relations to main entities selected in the app
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Verification status
    is_active = Column(Boolean, default=False)  # False until verified
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="corporate_profile")
    location = relationship("Location", back_populates="corporate_profiles")
    full_time_jobs = relationship("FullTimeJob", back_populates="company", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="corporate_profile", cascade="all, delete-orphan")
    followers = relationship("CorporateProfileFollow", back_populates="corporate_profile", cascade="all, delete-orphan")
    category = relationship("Category", lazy="joined", foreign_keys=[category_id])

    def __repr__(self):
        return f"<CorporateProfile(id={self.id}, company_name='{self.company_name}', user_id={self.user_id})>"
