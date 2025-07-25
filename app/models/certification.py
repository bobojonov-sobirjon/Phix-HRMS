from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Certification(Base):
    __tablename__ = "certifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=False)
    from_date = Column(DateTime(timezone=True), nullable=True)
    to_date = Column(DateTime(timezone=True), nullable=True)
    certificate_id = Column(String(255), nullable=True)
    certificate_path = Column(Text, nullable=True)
    certification_center_id = Column(Integer, ForeignKey('certification_centers.id'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationship
    user = relationship('User', back_populates='certifications')
    certification_center_ref = relationship('CertificationCenter', back_populates='certifications') 