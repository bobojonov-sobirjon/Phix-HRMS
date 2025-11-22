from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..schemas.auth import (
    UserRegister, UserLogin, SocialLogin, OTPRequest, 
    OTPVerify, PasswordResetVerified, LoginResponse, UserResponse, 
    Token, OTPResponse, UserUpdate, RegisterOTPRequest, 
    RegisterOTPVerify, RegisterResponse, RefreshTokenRequest, 
    RefreshTokenResponse, UserRestore
)
from ..schemas.profile import UserFullResponse, RoleResponse
from ..schemas.common import SuccessResponse, ErrorResponse
from ..repositories.user_repository import UserRepository, OTPRepository
from ..repositories.role_repository import RoleRepository
from ..repositories.team_member_repository import TeamMemberRepository
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..utils.auth import create_access_token, create_refresh_token, verify_password, verify_refresh_token, oauth2_scheme
from ..utils.email import generate_otp, send_otp_email, send_registration_otp_email
from ..utils.social_auth import verify_social_token
from ..utils.device_token_logger import create_user_device_token
from ..models.user import User
from ..models.role import Role
from ..models.otp import OTP
from datetime import timedelta
from ..config import settings
import os
import base64
from io import BytesIO
from json import JSONDecodeError

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Dependency to get current user from token (for manual header usage)
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
            detail="User does not exist"
        )
    
    return user

# Dependency to get current user including deleted users (for restore operations)
def get_current_user_including_deleted(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token including deleted users"""
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
    
    # Get user including deleted users
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist"
        )
    
    return user

# Dependency to get current user from OAuth2 token (for Swagger UI)
def get_current_user_oauth2(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from OAuth2 token (for Swagger UI)"""
    from ..utils.auth import verify_token
    
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
            detail="User does not exist"
        )
    
    return user

@router.post("/register", response_model=SuccessResponse)
async def register(user_data: RegisterOTPRequest, db: Session = Depends(get_db)):
    """Register new user - send OTP for email verification"""
    try:
        user_repo = UserRepository(db)
        otp_repo = OTPRepository(db)

        existing_user = user_repo.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            if existing_user.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email was deleted and cannot be registered again"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
        
        if user_data.phone:
            existing_phone_user = user_repo.db.query(User).filter(User.phone == user_data.phone).first()
            if existing_phone_user:
                if existing_phone_user.is_deleted:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User with this phone number was deleted and cannot be registered again"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User with this phone number already exists"
                    )
        
        otp_code = generate_otp(settings.OTP_LENGTH)
        
        registration_data = {
            "name": user_data.name,
            "email": user_data.email,
            "password": user_data.password,
            "phone": user_data.phone,
            "device_token": user_data.device_token,
            "device_type": user_data.device_type
        }
        
        otp = otp_repo.create_otp_with_data(user_data.email, otp_code, "registration", registration_data)
        
        email_sent = await send_registration_otp_email(user_data.email, otp_code)
        
        print(f"Email sending result: {email_sent}")
        
        if not email_sent:
            return SuccessResponse(
                msg="Registration OTP code generated (email failed, check console for OTP)",
                data={
                    "email": user_data.email,
                    "otp_code": otp_code
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
        
        otp = otp_repo.get_valid_otp_by_type(otp_verify.email, otp_verify.otp_code, "registration")
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired registration OTP code"
            )
        
        existing_user = user_repo.db.query(User).filter(User.email == otp_verify.email).first()
        if existing_user:
            if existing_user.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email was deleted and cannot be registered again"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
        
        registration_data = otp.get_data()
        if not registration_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration data"
            )
        
        if registration_data.get("phone"):
            existing_phone_user = user_repo.db.query(User).filter(User.phone == registration_data["phone"]).first()
            if existing_phone_user:
                if existing_phone_user.is_deleted:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User with this phone number was deleted and cannot be registered again"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User with this phone number already exists"
                    )
        
        user = user_repo.create_user(
            name=registration_data["name"],
            email=registration_data["email"],
            password=registration_data["password"],
            phone=registration_data["phone"]
        )
        
        otp_repo.mark_otp_used(otp.id)
        
        user_repo.assign_roles_to_user(user.id, ['user', 'admin'])
        
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        user_repo.update_last_login(user.id)
        
        # Create device token if provided
        if otp_verify.device_token and otp_verify.device_type:
            create_user_device_token(
                db=db,
                user_id=user.id,
                device_token=otp_verify.device_token,
                device_type=otp_verify.device_type
            )
        # Also check registration_data for device_token (in case it was saved during register step)
        elif registration_data.get("device_token") and registration_data.get("device_type"):
            create_user_device_token(
                db=db,
                user_id=user.id,
                device_token=registration_data.get("device_token"),
                device_type=registration_data.get("device_type")
            )
        
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

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token endpoint for Swagger UI"""
    try:
        user_repo = UserRepository(db)
        
        user = user_repo.get_user_by_email(form_data.username)  # OAuth2PasswordRequestForm uses 'username' field
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        
        user_repo.update_last_login(user.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
        
        user = user_repo.get_user_by_email(user_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User does not exist"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        if not user.verify_password(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        user_repo.update_last_login(user.id)
        
        # Create device token if provided (using logging utility)
        if user_data.device_token and user_data.device_type:
            print(f"[Login] Creating device token for user {user.id}, device_type: {user_data.device_type}")
            create_user_device_token(
                db=db,
                user_id=user.id,
                device_token=user_data.device_token,
                device_type=user_data.device_type
            )
        else:
            print(f"[Login] Device token not provided for user {user.id}")
        
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
        
        social_user_info = verify_social_token(social_data.provider, social_data.access_token)
        if not social_user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid social token"
            )
        
        user = user_repo.get_user_by_social_id(social_data.provider, social_user_info["id"])
        
        if not user:
            user = user_repo.db.query(User).filter(User.email == social_user_info["email"]).first()
            
            if user:
                if user.is_deleted:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User with this email was deleted and cannot login"
                    )
                if social_data.provider == "google":
                    user.google_id = social_user_info["id"]
                elif social_data.provider == "facebook":
                    user.facebook_id = social_user_info["id"]
                elif social_data.provider == "apple":
                    user.apple_id = social_user_info["id"]
                
                user.is_verified = True
                db.commit()
            else:
                user = user_repo.create_social_user(
                    name=social_user_info["name"],
                    email=social_user_info["email"],
                    provider=social_data.provider,
                    social_id=social_user_info["id"],
                    avatar_url=social_user_info.get("picture")
                )
                user_repo.assign_roles_to_user(user.id, ['user', 'admin'])
        
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
         
        user = user_repo.get_user_by_email(otp_request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found"
            )
        
        otp_code = generate_otp(settings.OTP_LENGTH)
        
        otp = otp_repo.create_otp(otp_request.email, otp_code)
        
        email_sent = await send_otp_email(otp_request.email, otp_code)
        
        if not email_sent:
            return SuccessResponse(
                msg="OTP code generated (email failed, check console for OTP)",
                data={
                    "email": otp_request.email,
                    "otp_code": otp_code
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
        
        otp = otp_repo.get_valid_otp(otp_verify.email, otp_verify.otp_code)
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code"
            )
        
        otp_repo.mark_otp_used(otp.id)
        
        return SuccessResponse(msg="OTP verified successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(password_reset: PasswordResetVerified, db: Session = Depends(get_db)):
    """Reset password after OTP verification (no OTP required in request)"""
    try:
        user_repo = UserRepository(db)
        
        user = user_repo.get_user_by_email(password_reset.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        verified_otp = db.query(OTP).filter(
            OTP.email == password_reset.email,
            OTP.otp_type == "password_reset",
            OTP.is_used == True
        ).order_by(OTP.created_at.desc()).first()
        
        if not verified_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No verified OTP found. Please verify OTP first using /verify-otp endpoint"
            )
        
        user_repo.update_user_password(user.id, password_reset.new_password)
        
        return SuccessResponse(msg="Password reset successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_user_oauth2), db: Session = Depends(get_db)):
    """Get current user full profile, with full avatar_url, full image URLs for project images, and full flag_image URL for location. Only one location object should be returned."""
    try:
        user_repo = UserRepository(db)
        full_user = user_repo.get_user_full_profile(current_user.id)
        if not full_user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = UserFullResponse.model_validate(full_user).dict()
        base_url = str(request.base_url).rstrip("/")
        if user_data["avatar_url"]:
            user_data["avatar_url"] = f"{base_url}{user_data['avatar_url']}"
        for project in user_data.get("projects", []):
            for img in project.get("images", []):
                if img["image"] and not img["image"].startswith("http"):
                    img["image"] = f"{base_url}{img['image']}"
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
            main_category_id=updated_user.main_category_id,
            sub_category_id=updated_user.sub_category_id,
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
        
        user = user_repo.get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User does not exist"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
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
        
        test_token = create_access_token(data={"sub": "1"})
        
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
    """Get all user profiles (personal + owned corporate + team memberships)"""
    from ..config import settings
    from ..models.corporate_profile import CorporateProfile
    from ..repositories.team_member_repository import TeamMemberRepository
    from ..repositories.corporate_profile_repository import CorporateProfileRepository
    from ..utils.permissions import get_role_permissions
    from ..models.team_member import TeamMemberRole
    
    profiles = []
    
    # 1. Personal Profile (har doim birinchi)
    personal_profile = {
        "id": f"personal_{current_user.id}",
        "type": "personal",
        "name": current_user.name,
        "role": "Personal Account",
        "avatar": f"{settings.BASE_URL}{current_user.avatar_url}" if current_user.avatar_url else None,
        "is_active": current_user.is_active,
        "is_owner": True,
        "can_create_jobs": False,  # Personal profile job yarata olmaydi
        "permissions": []
    }
    profiles.append(personal_profile)
    
    # 2. Owned Corporate Profile
    corporate_profile_repo = CorporateProfileRepository(db)
    user_corporate_profile = corporate_profile_repo.get_by_user_id(current_user.id)
    
    if user_corporate_profile:
        owned_profile = {
            "id": f"corporate_{user_corporate_profile.id}",
            "type": "corporate",
            "name": user_corporate_profile.company_name,
            "role": "Owner",
            "avatar": f"{settings.BASE_URL}{user_corporate_profile.logo_url}" if user_corporate_profile.logo_url else None,
            "is_active": user_corporate_profile.is_active and user_corporate_profile.is_verified,
            "is_owner": True,
            "can_create_jobs": user_corporate_profile.is_active and user_corporate_profile.is_verified,
            "corporate_profile_id": user_corporate_profile.id,
            "permissions": [p.value for p in get_role_permissions(TeamMemberRole.OWNER)]
        }
        profiles.append(owned_profile)
    
    # 3. Team Memberships (boshqa kompaniyalarda - faqat owned corporate profilidan tashqarida)
    team_member_repo = TeamMemberRepository(db)
    user_team_memberships = team_member_repo.get_user_team_memberships_accepted(current_user.id)
    
    # User's owned corporate profile ID - exclude it from team memberships
    owned_corporate_profile_id = user_corporate_profile.id if user_corporate_profile else None
    
    for membership in user_team_memberships:
        # Skip if this is the user's own corporate profile (it's already added as owned profile)
        if owned_corporate_profile_id and membership.corporate_profile_id == owned_corporate_profile_id:
            continue
            
        corporate_profile = db.query(CorporateProfile).filter(
            CorporateProfile.id == membership.corporate_profile_id
        ).first()
        
        if corporate_profile and corporate_profile.is_active and corporate_profile.is_verified and not corporate_profile.is_deleted:
            # Role-based permissions
            permissions = [p.value for p in get_role_permissions(membership.role)]
            
            team_profile = {
                "id": f"team_{membership.id}",
                "type": "team_member",
                "name": corporate_profile.company_name,
                "role": membership.role.value,
                "avatar": f"{settings.BASE_URL}{corporate_profile.logo_url}" if corporate_profile.logo_url else None,
                "is_active": True,
                "is_owner": False,
                "can_create_jobs": "create_job" in permissions,
                "corporate_profile_id": corporate_profile.id,
                "team_member_id": membership.id,
                "permissions": permissions
            }
            profiles.append(team_profile)
    
    return SuccessResponse(
        status="success",
        msg="User profiles retrieved successfully",
        data={"profiles": profiles}
    )

@router.post("/restore-user", response_model=SuccessResponse)
async def restore_user(
    restore_data: UserRestore, 
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Restore deleted user by email (set is_deleted to False) - Optional authentication"""
    try:
        user_repo = UserRepository(db)
        
        # Optional authentication - if token provided, verify it
        if authorization:
            try:
                current_user = get_current_user_including_deleted(authorization, db)
                # User is authenticated, can proceed
            except HTTPException:
                # Invalid token, but we still allow the operation
                pass
        
        # Check if user exists with this email (including deleted users)
        user = db.query(User).filter(User.email == restore_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found"
            )
        
        # Check if user is already active (not deleted)
        if not user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active (not deleted)"
            )
        
        # Restore user
        success = user_repo.restore_user_by_email(restore_data.email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore user"
            )
        
        return SuccessResponse(
            msg="User restored successfully",
            data={"email": restore_data.email}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 