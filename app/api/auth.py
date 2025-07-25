from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..schemas.auth import (
    UserRegister, UserLogin, SocialLogin, OTPRequest, 
    OTPVerify, PasswordReset, LoginResponse, UserResponse, 
    Token, OTPResponse, UserUpdate
)
from ..schemas.profile import UserFullResponse, RoleResponse
from ..repositories.user_repository import UserRepository, OTPRepository
from ..repositories.role_repository import RoleRepository
from ..utils.auth import create_access_token, verify_password
from ..utils.email import generate_otp, send_otp_email
from ..utils.social_auth import verify_social_token
from ..models.user import User
from ..models.role import Role
from datetime import timedelta
from ..config import settings
import os
import base64
from io import BytesIO
from json import JSONDecodeError

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Dependency to get current user from token
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token"""
    from ..utils.auth import verify_token
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/register", response_model=LoginResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user with email and password"""
    user_repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = user_repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = user_repo.create_user(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password
    )
    
    # Assign default user role
    role_repo = RoleRepository(db)  # Assuming RoleRepository is imported
    user_role = role_repo.get_role_by_name('user')
    if user_role:
        user_repo.assign_role_to_user(user.id, user_role.id)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    
    # Update last login
    user_repo.update_last_login(user.id)
    
    return LoginResponse(
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_social_user=user.is_social_user,
            created_at=user.created_at,
            last_login=user.last_login,
            phone=user.phone,
            raw_avatar_url=user.avatar_url,
            about_me=user.about_me,
            current_position=user.current_position,
            location_id=user.location_id,
            roles=[role.name for role in user.roles]
        ),
        token=Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )

@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password"""
    user_repo = UserRepository(db)
    
    # Get user by email
    user = user_repo.get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    
    # Update last login
    user_repo.update_last_login(user.id)
    
    return LoginResponse(
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_social_user=user.is_social_user,
            created_at=user.created_at,
            last_login=user.last_login,
            phone=user.phone,
            raw_avatar_url=user.avatar_url,
            about_me=user.about_me,
            current_position=user.current_position,
            location_id=user.location_id,
            roles=[role.name for role in user.roles]
        ),
        token=Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )

@router.post("/social-login", response_model=LoginResponse)
async def social_login(social_data: SocialLogin, db: Session = Depends(get_db)):
    """Login or register user via social login (Google, Facebook, Apple)"""
    user_repo = UserRepository(db)
    
    # Verify social token
    social_user_info = verify_social_token(social_data.provider, social_data.access_token)
    if not social_user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid social token"
        )
    
    # Check if user exists by social ID
    user = user_repo.get_user_by_social_id(social_data.provider, social_user_info["id"])
    
    if not user:
        # Check if user exists by email
        user = user_repo.get_user_by_email(social_user_info["email"])
        
        if user:
            # Link social account to existing user
            if social_data.provider == "google":
                user.google_id = social_user_info["id"]
            elif social_data.provider == "facebook":
                user.facebook_id = social_user_info["id"]
            elif social_data.provider == "apple":
                user.apple_id = social_user_info["id"]
            
            user.is_verified = True
            db.commit()
        else:
            # Create new user
            user = user_repo.create_social_user(
                name=social_user_info["name"],
                email=social_user_info["email"],
                provider=social_data.provider,
                social_id=social_user_info["id"],
                avatar_url=social_user_info.get("picture")
            )
            # Assign default user role
            role_repo = RoleRepository(db)
            user_role = role_repo.get_role_by_name('user')
            if user_role:
                user_repo.assign_role_to_user(user.id, user_role.id)
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    
    # Update last login
    user_repo.update_last_login(user.id)
    
    return LoginResponse(
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_social_user=user.is_social_user,
            created_at=user.created_at,
            last_login=user.last_login,
            phone=user.phone,
            raw_avatar_url=user.avatar_url,
            about_me=user.about_me,
            current_position=user.current_position,
            location_id=user.location_id,
            roles=[role.name for role in user.roles]
        ),
        token=Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )

@router.post("/forgot-password", response_model=OTPResponse)
async def forgot_password(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP code to user's email for password reset"""
    user_repo = UserRepository(db)
    otp_repo = OTPRepository(db)
    
    # Check if user exists
    user = user_repo.get_user_by_email(otp_request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found"
        )
    
    # Generate OTP
    otp_code = generate_otp(settings.OTP_LENGTH)
    
    # Create OTP record
    otp = otp_repo.create_otp(otp_request.email, otp_code)
    
    # Send OTP via email
    email_sent = send_otp_email(otp_request.email, otp_code)
    if not email_sent:
        # For development/testing, return OTP in response instead of failing
        print(f"⚠️  Email sending failed, but returning OTP for testing: {otp_code}")
        return OTPResponse(
            message="OTP code generated (email failed, check console for OTP)",
            email=otp_request.email,
            otp_code=otp_code  # Include OTP in response for testing
        )
    
    return OTPResponse(
        message="OTP code sent to your email",
        email=otp_request.email
    )

@router.post("/verify-otp", response_model=dict)
async def verify_otp(otp_verify: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP code for password reset"""
    otp_repo = OTPRepository(db)
    
    # Get valid OTP
    otp = otp_repo.get_valid_otp(otp_verify.email, otp_verify.otp_code)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )
    
    # Mark OTP as used
    otp_repo.mark_otp_used(otp.id)
    
    return {"message": "OTP verified successfully"}

@router.post("/reset-password", response_model=dict)
async def reset_password(password_reset: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using OTP verification"""
    user_repo = UserRepository(db)
    otp_repo = OTPRepository(db)
    
    # Verify OTP
    otp = otp_repo.get_valid_otp(password_reset.email, password_reset.otp_code)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )
    
    # Get user
    user = user_repo.get_user_by_email(password_reset.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user_repo.update_user_password(user.id, password_reset.new_password)
    
    # Mark OTP as used
    otp_repo.mark_otp_used(otp.id)
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserFullResponse)
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user full profile, with full avatar_url, full image URLs for project images, and full flag_image URL for location. Only one location object should be returned."""
    user_repo = UserRepository(db)
    full_user = user_repo.get_user_full_profile(current_user.id)
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = UserFullResponse.from_orm(full_user).dict()
    base_url = str(request.base_url).rstrip("/")
    # Fix avatar_url
    if user_data["avatar_url"]:
        user_data["avatar_url"] = f"{base_url}{user_data['avatar_url']}"
    # Fix project images
    for project in user_data.get("projects", []):
        for img in project.get("images", []):
            if img["image"] and not img["image"].startswith("http"):
                img["image"] = f"{base_url}{img['image']}"
    # Fix location flag_image and remove location_id
    if user_data.get("location"):
        if user_data["location"].get("flag_image") and not user_data["location"]["flag_image"].startswith("http"):
            user_data["location"]["flag_image"] = f"{base_url}{user_data['location']['flag_image']}"
    user_data.pop("location_id", None)
    return user_data

@router.patch("/me", response_model=UserResponse)
async def update_profile(update: UserUpdate, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile fields (text fields only). Use /profile/avatar for avatar uploads. Returns full avatar_url."""
    # Remove avatar_base64 if present
    update_dict = update.dict(exclude_unset=True)
    update_dict.pop("avatar_base64", None)
    user_repo = UserRepository(db)
    updated_user = user_repo.update_user_profile(current_user.id, update_dict)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = UserResponse(
        id=updated_user.id,
        name=updated_user.name,
        email=updated_user.email,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        is_social_user=updated_user.is_social_user,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login,
        phone=updated_user.phone,
        raw_avatar_url=updated_user.avatar_url,
        about_me=updated_user.about_me,
        current_position=updated_user.current_position,
        location_id=updated_user.location_id,
        roles=[role.name for role in updated_user.roles]
    ).dict()
    if user_data["raw_avatar_url"]:
        base_url = str(request.base_url).rstrip("/")
        user_data["avatar_url"] = f"{base_url}{user_data['raw_avatar_url']}"
    else:
        user_data["avatar_url"] = None
    user_data.pop("avatar_base64", None)
    return user_data

@router.delete("/me", response_model=dict)
async def delete_account(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Delete current user account (soft delete)"""
    user_repo = UserRepository(db)
    
    if not user_repo.soft_delete_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Account deleted successfully"}

@router.post("/test-token")
async def test_token_generation(db: Session = Depends(get_db)):
    """Test endpoint to generate a valid token for testing"""
    from ..utils.auth import create_access_token
    
    # Create a test token
    test_token = create_access_token(data={"sub": "1"})
    
    return {
        "message": "Test token generated",
        "token": test_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    } 