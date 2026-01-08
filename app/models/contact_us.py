from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.database import Base

class ContactUs(Base):
    __tablename__ = 'contact_us'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact_type = Column(String(50), nullable=False)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 