from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from ..db.database import Base
import enum


class DeviceType(str, enum.Enum):
    IOS = "ios"
    ANDROID = "android"


class UserDeviceToken(Base):
    __tablename__ = "user_device_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    device_token = Column(Text, nullable=False)
    device_type = Column(
        PG_ENUM('ios', 'android', name='devicetype', create_type=False),
        nullable=False
    )
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="device_tokens")
    
    def __repr__(self):
        return f"<UserDeviceToken(id={self.id}, user_id={self.user_id}, device_type='{self.device_type}', is_active={self.is_active})>"

