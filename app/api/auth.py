from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..schemas.auth import (
    UserRegister, UserLogin, SocialLogin, OTPRequest, 
    OTPVerify, PasswordReset, LoginResponse, UserResponse, 
    Token, OTPResponse, UserUpdate, RegisterOTPRequest, 
    RegisterOTPVerify, RegisterResponse, RefreshTokenRequest, 
    RefreshTokenResponse
)
from ..schemas.profile import UserFullResponse, RoleResponse
from ..schemas.common import SuccessResponse, ErrorResponse
from ..repositories.user_repository import UserRepository, OTPRepository
from ..repositories.role_repository import RoleRepository
from ..repositories.team_member_repository import TeamMemberRepository
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..utils.auth import create_access_token, create_refresh_token, verify_password, verify_refresh_token
from ..utils.email import generate_otp, send_otp_email, send_registration_otp_email
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

@router.post("/register", response_model=SuccessResponse)
async def register(user_data: RegisterOTPRequest, db: Session = Depends(get_db)):
    """Register new user - send OTP for email verification"""
    try:
        user_repo = UserRepository(db)
        otp_repo = OTPRepository(db)
        
        # Check if user already exists
        existing_user = user_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check if phone already exists (only if phone is provided)
        if user_data.phone:
            existing_phone_user = user_repo.get_user_by_phone(user_data.phone)
            if existing_phone_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists"
                )
        
        # Generate OTP for registration
        otp_code = generate_otp(settings.OTP_LENGTH)
        
        # Create OTP record for registration with user data
        registration_data = {
            "name": user_data.name,
            "email": user_data.email,
            "password": user_data.password,
            "phone": user_data.phone
        }
        otp = otp_repo.create_otp_with_data(user_data.email, otp_code, "registration", registration_data)
        
        # Print email configuration for debugging
        print("=== EMAIL DEBUG INFO ===")
        print(f"SMTP_SERVER: {settings.SMTP_SERVER}")
        print(f"SMTP_PORT: {settings.SMTP_PORT}")
        print(f"SMTP_USERNAME: {settings.SMTP_USERNAME}")
        print(f"SMTP_PASSWORD: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'NOT SET'}")
        print(f"Recipient Email: {user_data.email}")
        print(f"OTP Code: {otp_code}")
        print("========================")
        
        # Send registration OTP via email
        email_sent = await send_registration_otp_email(user_data.email, otp_code)
        
        print(f"Email sending result: {email_sent}")
        
        if not email_sent:
            # For development/testing, return OTP in response instead of failing
            return SuccessResponse(
                msg="Registration OTP code generated (email failed, check console for OTP)",
                data={
                    "email": user_data.email,
                    "otp_code": otp_code  # Include OTP in response for testing
                }
            )
        
        return SuccessResponse(
            msg="Registration OTP code sent to your email",
            data={"email": user_data.email}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register-code-check", response_model=SuccessResponse)
async def verify_registration_otp(otp_verify: RegisterOTPVerify, db: Session = Depends(get_db)):
    """Verify registration OTP and create user account"""
    try:
        user_repo = UserRepository(db)
        otp_repo = OTPRepository(db)
        
        # Get valid registration OTP
        otp = otp_repo.get_valid_otp_by_type(otp_verify.email, otp_verify.otp_code, "registration")
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired registration OTP code"
            )
        
        # Check if user already exists (double check)
        existing_user = user_repo.get_user_by_email(otp_verify.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Get user data from OTP
        registration_data = otp.get_data()
        if not registration_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration data"
            )
        
        # Check if phone already exists (only if phone is provided)
        if registration_data["phone"]:
            existing_phone_user = user_repo.get_user_by_phone(registration_data["phone"])
            if existing_phone_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists"
                )
        
        # Create new user with stored data
        user = user_repo.create_user(
            name=registration_data["name"],
            email=registration_data["email"],
            password=registration_data["password"],
            phone=registration_data["phone"]
        )
        
        # Mark OTP as used
        otp_repo.mark_otp_used(otp.id)
        
        # Assign default user and admin roles
        user_repo.assign_roles_to_user(user.id, ['user', 'admin'])
        
        # Create access token and refresh token
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Update last login
        user_repo.update_last_login(user.id)
        
        login_response = LoginResponse(
            token=Token(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
            refresh_token=refresh_token
        )
        
        return SuccessResponse(
            msg="Registration completed successfully",
            data=login_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=SuccessResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password"""
    try:
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
        
        # Create access token and refresh token
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Update last login
        user_repo.update_last_login(user.id)
        
        login_response = LoginResponse(
            token=Token(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
            refresh_token=refresh_token
        )
        
        return SuccessResponse(
            msg="Login successful",
            data=login_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social-login", response_model=SuccessResponse)
async def social_login(social_data: SocialLogin, db: Session = Depends(get_db)):
    """Login or register user via social login (Google, Facebook, Apple)"""
    try:
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
                # Assign default user and admin roles
                user_repo.assign_roles_to_user(user.id, ['user', 'admin'])
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create access token and refresh token
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Update last login
        user_repo.update_last_login(user.id)
        
        login_response = LoginResponse(
            token=Token(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
            refresh_token=refresh_token
        )
        
        return SuccessResponse(
            msg="Social login successful",
            data=login_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP code to user's email for password reset"""
    try:
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
        email_sent = await send_otp_email(otp_request.email, otp_code)
        
        if not email_sent:
            # For development/testing, return OTP in response instead of failing
            return SuccessResponse(
                msg="OTP code generated (email failed, check console for OTP)",
                data={
                    "email": otp_request.email,
                    "otp_code": otp_code  # Include OTP in response for testing
                }
            )
        
        return SuccessResponse(
            msg="OTP code sent to your email",
            data={"email": otp_request.email}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-otp", response_model=SuccessResponse)
async def verify_otp(otp_verify: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP code for password reset"""
    try:
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
        
        return SuccessResponse(msg="OTP verified successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(password_reset: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using OTP verification"""
    try:
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
        
        return SuccessResponse(msg="Password reset successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user full profile, with full avatar_url, full image URLs for project images, and full flag_image URL for location. Only one location object should be returned."""
    try:
        user_repo = UserRepository(db)
        full_user = user_repo.get_user_full_profile(current_user.id)
        if not full_user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = UserFullResponse.model_validate(full_user).dict()
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
        return SuccessResponse(
            msg="User profile retrieved successfully",
            data=user_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/me", response_model=SuccessResponse)
async def update_profile(update: UserUpdate, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile fields (text fields only). Use /profile/avatar for avatar uploads. Returns full avatar_url."""
    try:
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
        return SuccessResponse(
            msg="Profile updated successfully",
            data=user_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/me", response_model=SuccessResponse)
async def delete_account(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Delete current user account (soft delete)"""
    try:
        user_repo = UserRepository(db)
        
        if not user_repo.soft_delete_user(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return SuccessResponse(msg="Account deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-token", response_model=SuccessResponse)
async def test_token_generation(db: Session = Depends(get_db)):
    """Test endpoint to generate a valid token for testing"""
    try:
        from ..utils.auth import create_access_token
        
        # Create a test token
        test_token = create_access_token(data={"sub": "1"})
        
        return SuccessResponse(
            msg="Test token generated",
            data={
                "token": test_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh-token", response_model=SuccessResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        user_repo = UserRepository(db)
        
        # Verify refresh token
        payload = verify_refresh_token(refresh_data.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = user_repo.get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create new access token and refresh token
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        refresh_response = RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return SuccessResponse(
            msg="Token refreshed successfully",
            data=refresh_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-login", response_model=SuccessResponse)
async def test_login(db: Session = Depends(get_db)):
    """Test login endpoint that returns a valid token"""
    try:
        from ..utils.auth import create_access_token
        
        # Create a test token
        test_token = create_access_token(data={"sub": "1"})
        
        # Create a mock user response
        mock_user = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "is_active": True,
            "is_verified": True,
            "is_social_user": False,
            "created_at": "2024-01-01T00:00:00",
            "last_login": "2024-01-01T00:00:00",
            "phone": None,
            "raw_avatar_url": None,
            "about_me": None,
            "current_position": None,
            "location_id": None,
            "roles": ["user", "admin"]
        }
        
        login_response = {
            "user": mock_user,
            "token": {
                "access_token": test_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
        
        return SuccessResponse(
            msg="Test login successful",
            data=login_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-profiles", response_model=SuccessResponse)
async def get_user_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's corporate profile and team member roles"""
    from ..config import settings
    from ..models.corporate_profile import CorporateProfile
    
    # Get user's own corporate profile (if exists)
    corporate_profile_repo = CorporateProfileRepository(db)
    user_corporate_profile = corporate_profile_repo.get_by_user_id(current_user.id)
    
    corporate_profile_data = None
    if user_corporate_profile:
        # Add base URL to profile data
        if user_corporate_profile.logo_url:
            user_corporate_profile.logo_url = f"{settings.BASE_URL}{user_corporate_profile.logo_url}"
        
        if user_corporate_profile.location and user_corporate_profile.location.flag_image:
            user_corporate_profile.location.flag_image = f"{settings.BASE_URL}{user_corporate_profile.location.flag_image}"
        
        if user_corporate_profile.user and user_corporate_profile.user.avatar_url:
            user_corporate_profile.user.avatar_url = f"{settings.BASE_URL}{user_corporate_profile.user.avatar_url}"
        
        # Prepare team members data
        team_members_data = []
        if hasattr(user_corporate_profile, 'team_members') and user_corporate_profile.team_members:
            for team_member in user_corporate_profile.team_members:
                if team_member.user and team_member.user.avatar_url:
                    team_member.user.avatar_url = f"{settings.BASE_URL}{team_member.user.avatar_url}"
                
                team_member_data = {
                    "id": team_member.id,
                    "user_id": team_member.user_id,
                    "user_name": team_member.user.name if team_member.user else "",
                    "user_email": team_member.user.email if team_member.user else "",
                    "user_avatar": team_member.user.avatar_url if team_member.user else None,
                    "role": team_member.role.value,
                    "status": team_member.status.value,
                    "invited_by_user_id": team_member.invited_by_user_id,
                    "invited_by_name": team_member.invited_by.name if team_member.invited_by else "",
                    "created_at": team_member.created_at,
                    "accepted_at": team_member.accepted_at,
                    "rejected_at": team_member.rejected_at
                }
                team_members_data.append(team_member_data)
        
        # Get user's role in their own corporate profile
        user_role_in_own_company = None
        if user_corporate_profile.team_members:
            for team_member in user_corporate_profile.team_members:
                if team_member.user_id == current_user.id:
                    user_role_in_own_company = {
                        "id": team_member.id,
                        "role": team_member.role.value,
                        "status": team_member.status.value,
                        "created_at": team_member.created_at,
                        "accepted_at": team_member.accepted_at,
                        "rejected_at": team_member.rejected_at
                    }
                    break
        
        corporate_profile_data = {
            "id": user_corporate_profile.id,
            "company_name": user_corporate_profile.company_name,
            "industry": user_corporate_profile.industry,
            "phone_number": user_corporate_profile.phone_number,
            "country_code": user_corporate_profile.country_code,
            "location_id": user_corporate_profile.location_id,
            "overview": user_corporate_profile.overview,
            "website_url": user_corporate_profile.website_url,
            "company_size": user_corporate_profile.company_size.value,
            "logo_url": user_corporate_profile.logo_url,
            "user_id": user_corporate_profile.user_id,
            "is_active": user_corporate_profile.is_active,
            "is_verified": user_corporate_profile.is_verified,
            "created_at": user_corporate_profile.created_at,
            "updated_at": user_corporate_profile.updated_at,
            "location": {
                "id": user_corporate_profile.location.id,
                "name": user_corporate_profile.location.name,
                "code": user_corporate_profile.location.code,
                "flag_image": user_corporate_profile.location.flag_image
            } if user_corporate_profile.location else None,
            "user": {
                "id": user_corporate_profile.user.id,
                "name": user_corporate_profile.user.name,
                "email": user_corporate_profile.user.email,
                "is_active": user_corporate_profile.user.is_active,
                "is_verified": user_corporate_profile.user.is_verified,
                "is_social_user": user_corporate_profile.user.is_social_user,
                "created_at": user_corporate_profile.user.created_at,
                "last_login": user_corporate_profile.user.last_login,
                "phone": user_corporate_profile.user.phone,
                "avatar_url": user_corporate_profile.user.avatar_url,
                "about_me": user_corporate_profile.user.about_me,
                "current_position": user_corporate_profile.user.current_position,
                "location_id": user_corporate_profile.user.location_id
            } if user_corporate_profile.user else None,
            "user_role": user_role_in_own_company,
            "team_members": team_members_data
        }
    
    # Get user's team memberships in other companies (all statuses)
    team_member_repo = TeamMemberRepository(db)
    user_team_memberships = team_member_repo.get_user_team_memberships_all_statuses(current_user.id)
    
    another_role_list = []
    for membership in user_team_memberships:
        # Get corporate profile details
        corporate_profile = db.query(CorporateProfile).filter(
            CorporateProfile.id == membership.corporate_profile_id
        ).first()
        
        if corporate_profile:
            # Add base URL to corporate profile logo
            logo_url = corporate_profile.logo_url
            if logo_url:
                logo_url = f"{settings.BASE_URL}{logo_url}"
            
            # Add base URL to location flag
            flag_image = None
            if corporate_profile.location and corporate_profile.location.flag_image:
                flag_image = f"{settings.BASE_URL}{corporate_profile.location.flag_image}"
            
            # Add base URL to user avatar
            user_avatar = current_user.avatar_url
            if user_avatar:
                user_avatar = f"{settings.BASE_URL}{user_avatar}"
            
            # Get corporate profile owner details
            corporate_profile_owner = None
            if corporate_profile.user:
                corporate_profile_owner = {
                    "id": corporate_profile.user.id,
                    "name": corporate_profile.user.name,
                    "email": corporate_profile.user.email,
                    "avatar_url": f"{settings.BASE_URL}{corporate_profile.user.avatar_url}" if corporate_profile.user.avatar_url else None,
                    "is_active": corporate_profile.user.is_active,
                    "is_verified": corporate_profile.user.is_verified,
                    "current_position": corporate_profile.user.current_position
                }
            
            another_role_list.append({
                "id": membership.id,
                "corporate_profile_id": membership.corporate_profile_id,
                "corporate_profile": {
                    "id": corporate_profile.id,
                    "company_name": corporate_profile.company_name,
                    "company_logo": logo_url,
                    "industry": corporate_profile.industry,
                    "overview": corporate_profile.overview,
                    "website_url": corporate_profile.website_url,
                    "company_size": corporate_profile.company_size.value,
                    "is_active": corporate_profile.is_active,
                    "is_verified": corporate_profile.is_verified,
                    "created_at": corporate_profile.created_at,
                    "location": {
                        "id": corporate_profile.location.id if corporate_profile.location else None,
                        "name": corporate_profile.location.name if corporate_profile.location else None,
                        "code": corporate_profile.location.code if corporate_profile.location else None,
                        "flag_image": flag_image
                    } if corporate_profile.location else None,
                    "owner": corporate_profile_owner
                },
                "user": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "email": current_user.email,
                    "avatar_url": user_avatar,
                    "is_active": current_user.is_active,
                    "is_verified": current_user.is_verified,
                    "current_position": current_user.current_position
                },
                "role": {
                    "id": membership.id,
                    "role": membership.role.value,
                    "status": membership.status.value,
                    "created_at": membership.created_at,
                    "accepted_at": membership.accepted_at,
                    "rejected_at": membership.rejected_at
                }
            })
    
    response_data = {
        "corporate_profile": corporate_profile_data,
        "another_role_list": another_role_list
    }
    
    return SuccessResponse(
        status="success",
        msg="User profiles retrieved successfully",
        data=response_data
    ) 