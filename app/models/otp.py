from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..db.database import Base
from datetime import datetime, timedelta, timezone
from ..core.config import settings
import json

class OTP(Base):
    __tablename__ = "otps"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # OTP details
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(10), nullable=False)
    otp_type = Column(String(50), nullable=False, default="password_reset")  # password_reset, registration, corporate_verification, etc.
    is_used = Column(Boolean, default=False)
    
    # Additional data (for storing registration info, etc.)
    data = Column(Text, nullable=True)
    
    # Expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def is_expired(self) -> bool:
        """Check if OTP has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if OTP is valid and not used"""
        return not self.is_used and not self.is_expired()
    
    def get_data(self) -> dict:
        """Get stored data as dictionary"""
        if self.data:
            try:
                return json.loads(self.data)
            except:
                return {}
        return {}
    
    def set_data(self, data: dict):
        """Set data as JSON string"""
        self.data = json.dumps(data)
    
    @classmethod
    def create_otp(cls, email: str, otp_code: str, otp_type: str = "password_reset", data: dict = None):
        """Create new OTP with expiration"""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        otp = cls(
            email=email,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        if data:
            otp.set_data(data)
        return otp 