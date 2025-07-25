from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base

class UserRole(Base):
    __tablename__ = 'user_roles'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False) 