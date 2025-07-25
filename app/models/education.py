from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Education(Base):
    __tablename__ = "educations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    degree = Column(String(255), nullable=False)
    education_facility_id = Column(Integer, ForeignKey('education_facilities.id'), nullable=True)
    from_date = Column(DateTime(timezone=True), nullable=True)
    to_date = Column(DateTime(timezone=True), nullable=True)
    is_graduate = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationship
    user = relationship('User', back_populates='educations')
    education_facility_ref = relationship('EducationFacility', back_populates='educations') 