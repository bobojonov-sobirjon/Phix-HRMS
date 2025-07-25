from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base
from datetime import datetime, timedelta
from ..config import settings

class OTP(Base):
    __tablename__ = "otps"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # OTP details
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(10), nullable=False)
    is_used = Column(Boolean, default=False)
    
    # Expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def is_expired(self) -> bool:
        """Check if OTP has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if OTP is valid and not used"""
        return not self.is_used and not self.is_expired()
    
    @classmethod
    def create_otp(cls, email: str, otp_code: str):
        """Create new OTP with expiration"""
        expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        return cls(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        ) 