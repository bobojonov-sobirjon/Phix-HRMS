from pydantic import BaseModel, EmailStr, validator, computed_field
from typing import Optional, List
from datetime import datetime
from ..config import settings
# from ..schemas.profile import RoleResponse

# Base User Schema
class UserBase(BaseModel):
    name: str
    email: EmailStr

# User Registration Schema
class UserRegister(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# User Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Social Login Schema
class SocialLogin(BaseModel):
    provider: str  # google, facebook, apple
    access_token: str

# OTP Request Schema
class OTPRequest(BaseModel):
    email: EmailStr

# OTP Verification Schema
class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

# Registration OTP Request Schema
class RegisterOTPRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# Registration OTP Verification Schema
class RegisterOTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

# Registration Response Schema
class RegisterResponse(BaseModel):
    message: str
    email: EmailStr
    otp_code: Optional[str] = None  # For development/testing

# Password Reset Schema
class PasswordReset(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# User Response Schema
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    is_verified: bool
    is_social_user: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    phone: Optional[str] = None
    raw_avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    location_id: Optional[int] = None
    roles: List[str] = []

    @computed_field(alias="avatar_url")
    @property
    def avatar_url(self) -> Optional[str]:
        if self.raw_avatar_url and not self.raw_avatar_url.startswith(('http://', 'https://')):
            return f"{settings.BASE_URL}{self.raw_avatar_url}"
        return self.raw_avatar_url

    class Config:
        from_attributes = True

# Login Response Schema
class LoginResponse(BaseModel):
    user: UserResponse
    token: Token

# OTP Response Schema
class OTPResponse(BaseModel):
    message: str
    email: EmailStr
    otp_code: Optional[str] = None  # For development/testing 

# User Update Schema
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    location_id: Optional[int] = None 