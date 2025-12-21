from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base

class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_title = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    from_date = Column(DateTime(timezone=True), nullable=True)
    to_date = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=False)
    industry = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    job_type = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationship
    user = relationship('User', back_populates='experiences')
    company_ref = relationship('Company', back_populates='experiences') 