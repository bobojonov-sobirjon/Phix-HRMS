from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    flag_image = Column(Text, nullable=True)
    code = Column(String(10), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    users = relationship('User', back_populates='location')
    corporate_profiles = relationship('CorporateProfile', back_populates='location')
    gig_jobs = relationship('GigJob', back_populates='location') 