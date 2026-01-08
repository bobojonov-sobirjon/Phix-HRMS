from pydantic import BaseModel, EmailStr, validator, computed_field
from typing import Optional, List
from datetime import datetime
from ..core.config import settings

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserRegister(UserBase):
    password: str
    phone: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, and plus sign')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_token: Optional[str] = None
    device_type: Optional[str] = None
    
    @validator('device_type')
    def validate_device_type(cls, v):
        if v is not None and v not in ['ios', 'android']:
            raise ValueError('device_type must be either "ios" or "android"')
        return v

class SocialLogin(BaseModel):
    provider: str
    access_token: str

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

class RegisterOTPRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    device_token: Optional[str] = None
    device_type: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('device_type')
    def validate_device_type(cls, v):
        if v is not None and v not in ['ios', 'android']:
            raise ValueError('device_type must be either "ios" or "android"')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, and plus sign')
        return v

class RegisterOTPVerify(BaseModel):
    email: EmailStr
    otp_code: str
    device_token: Optional[str] = None
    device_type: Optional[str] = None
    
    @validator('device_type')
    def validate_device_type(cls, v):
        if v is not None and v not in ['ios', 'android']:
            raise ValueError('device_type must be either "ios" or "android"')
        return v

class RegisterResponse(BaseModel):
    message: str
    email: EmailStr
    otp_code: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class PasswordResetVerified(BaseModel):
    email: EmailStr
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

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
    main_category_id: Optional[int] = None
    sub_category_id: Optional[int] = None
    roles: List[str] = []

    @computed_field(alias="avatar_url")
    @property
    def avatar_url(self) -> Optional[str]:
        if self.raw_avatar_url and not self.raw_avatar_url.startswith(('http://', 'https://')):
            return f"{settings.BASE_URL}{self.raw_avatar_url}"
        return self.raw_avatar_url

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    token: Token
    refresh_token: Optional[str] = None

class OTPResponse(BaseModel):
    message: str
    email: EmailStr
    otp_code: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    location_id: Optional[int] = None
    main_category_id: Optional[int] = None
    sub_category_id: Optional[int] = None

class UserRestore(BaseModel):
    email: EmailStr 