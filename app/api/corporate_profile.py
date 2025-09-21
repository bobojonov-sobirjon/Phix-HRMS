from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path
from ..database import get_db
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..repositories.user_repository import UserRepository
from ..schemas.corporate_profile import (
    CorporateProfileCreate,
    CorporateProfileUpdate,
    CorporateProfileResponse,
    CorporateProfileVerification,
    CorporateProfileListResponse,
    CompanySize
)
from ..schemas.common import MessageResponse, SuccessResponse
from ..utils.auth import get_current_user
from ..utils.email import send_email_with_retry, send_corporate_verification_email
from ..config import settings
from ..models.otp import OTP
import random
import string

router = APIRouter(prefix="/corporate-profile", tags=["Corporate Profile"])


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def save_logo_file(logo_file: UploadFile, profile_id: int) -> str:
    """Save logo file and return the URL"""
    # Create uploads directory if it doesn't exist
    upload_dir = Path("static/logos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = logo_file.filename.split('.')[-1] if logo_file.filename else 'jpg'
    unique_filename = f"logo_{profile_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = logo_file.file.read()
        buffer.write(content)
    
    # Return the URL
    return f"/static/logos/{unique_filename}"


def add_base_url_to_profile(profile):
    """Add base URL to logo_url, location.flag_image, user.avatar_url, and team member avatars"""
    if profile.logo_url:
        profile.logo_url = f"{settings.BASE_URL}{profile.logo_url}"
    
    if profile.location and profile.location.flag_image:
        profile.location.flag_image = f"{settings.BASE_URL}{profile.location.flag_image}"
    
    if profile.user and profile.user.avatar_url:
        profile.user.avatar_url = f"{settings.BASE_URL}{profile.user.avatar_url}"
    
    # Add base URL to team member avatars
    if hasattr(profile, 'team_members') and profile.team_members:
        for team_member in profile.team_members:
            if team_member.user and team_member.user.avatar_url:
                team_member.user.avatar_url = f"{settings.BASE_URL}{team_member.user.avatar_url}"
    
    return profile


def convert_profile_to_response(profile_with_urls):
    """Convert CorporateProfile model to CorporateProfileResponse format"""
    from ..schemas.corporate_profile import CorporateProfileResponse, TeamMemberResponse
    
    # Prepare team members data
    team_members_data = []
    if hasattr(profile_with_urls, 'team_members') and profile_with_urls.team_members:
        for team_member in profile_with_urls.team_members:
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
    
    # Create profile data with team members
    profile_dict = {
        "id": profile_with_urls.id,
        "company_name": profile_with_urls.company_name,
        "industry": profile_with_urls.industry,
        "phone_number": profile_with_urls.phone_number,
        "country_code": profile_with_urls.country_code,
        "location_id": profile_with_urls.location_id,
        "overview": profile_with_urls.overview,
        "website_url": profile_with_urls.website_url,
        "company_size": profile_with_urls.company_size.value,
        "logo_url": profile_with_urls.logo_url,
        "user_id": profile_with_urls.user_id,
        "is_active": profile_with_urls.is_active,
        "is_verified": profile_with_urls.is_verified,
        "created_at": profile_with_urls.created_at,
        "updated_at": profile_with_urls.updated_at,
        "location": {
            "id": profile_with_urls.location.id,
            "name": profile_with_urls.location.name,
            "code": profile_with_urls.location.code,
            "flag_image": profile_with_urls.location.flag_image
        } if profile_with_urls.location else None,
        "user": {
            "id": profile_with_urls.user.id,
            "name": profile_with_urls.user.name,
            "email": profile_with_urls.user.email,
            "is_active": profile_with_urls.user.is_active,
            "is_verified": profile_with_urls.user.is_verified,
            "is_social_user": profile_with_urls.user.is_social_user,
            "created_at": profile_with_urls.user.created_at,
            "last_login": profile_with_urls.user.last_login,
            "phone": profile_with_urls.user.phone,
            "avatar_url": profile_with_urls.user.avatar_url,
            "about_me": profile_with_urls.user.about_me,
            "current_position": profile_with_urls.user.current_position,
            "location_id": profile_with_urls.user.location_id
        } if profile_with_urls.user else None,
        "team_members": team_members_data
    }
    
    return CorporateProfileResponse(**profile_dict)


@router.post("/", response_model=SuccessResponse, tags=["Corporate Profile"])
async def create_corporate_profile(
    company_name: str = Form(...),
    industry: str = Form(...),
    phone_number: str = Form(...),
    country_code: str = Form(default="+1"),
    location_id: int = Form(...),
    overview: str = Form(...),
    website_url: Optional[str] = Form(None),
    company_size: CompanySize = Form(...),
    logo: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new corporate profile with logo upload"""
    from ..models.location import Location
    
    user_repo = UserRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if user already has a corporate profile
    if corporate_repo.check_user_has_profile(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a corporate profile"
        )
    
    # Validate location exists
    location = db.query(Location).filter(Location.id == location_id, Location.is_deleted == False).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid location ID"
        )
    
    # Validate logo file if provided
    logo_url = None
    if logo:
        if not logo.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed for logo"
            )
    
    # Create corporate profile data
    profile_data = CorporateProfileCreate(
        company_name=company_name,
        industry=industry,
        phone_number=phone_number,
        country_code=country_code,
        location_id=location_id,
        overview=overview,
        website_url=website_url,
        company_size=company_size,
        logo_url=None  # Will be set after saving
    )
    
    # Create corporate profile
    db_profile = corporate_repo.create(profile_data, current_user.id)
    
    # Handle logo upload if provided
    if logo:
        try:
            logo_url = save_logo_file(logo, db_profile.id)
            # Update profile with logo URL
            db_profile.logo_url = logo_url
            db.commit()
        except Exception as e:
            # If logo upload fails, delete the profile
            db.delete(db_profile)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload logo: {str(e)}"
            )
    
    # Generate and send OTP
    otp_code = generate_otp()
    otp = OTP.create_otp(
        email=current_user.email,
        otp_code=otp_code,
        otp_type="corporate_verification",
        data={"profile_id": db_profile.id}
    )
    
    db.add(otp)
    db.commit()
    
    # Create owner team member for the creator
    try:
        from ..repositories.team_member_repository import TeamMemberRepository
        team_repo = TeamMemberRepository(db)
        team_repo.create_owner_member(
            corporate_profile_id=db_profile.id,
            user_id=current_user.id
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to create owner team member: {e}")
    
    # Send verification email using dedicated corporate verification function
    try:
        await send_corporate_verification_email(
            email=current_user.email,
            otp_code=otp_code
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send corporate verification email: {e}")
    
    return SuccessResponse(
        msg="Corporate profile created successfully. Please check your email for verification code.",
        data={"profile_id": db_profile.id}
    )




@router.get("/", response_model=CorporateProfileListResponse, tags=["Corporate Profile"])
async def get_corporate_profiles(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    """Get all corporate profiles with pagination"""
    corporate_repo = CorporateProfileRepository(db)
    skip = (page - 1) * size

    profiles = corporate_repo.get_all(skip=skip, limit=size)
    total = corporate_repo.count_total()

    # Add base URL to all profiles and convert to response format
    profiles_with_urls = [add_base_url_to_profile(profile) for profile in profiles]
    profiles_response = [convert_profile_to_response(profile) for profile in profiles_with_urls]

    return CorporateProfileListResponse(
        corporate_profiles=profiles_response,
        total=total,
        page=page,
        size=size
    )


@router.get("/active", response_model=CorporateProfileListResponse, tags=["Corporate Profile"])
async def get_active_corporate_profiles(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    """Get only active corporate profiles"""
    corporate_repo = CorporateProfileRepository(db)
    skip = (page - 1) * size

    profiles = corporate_repo.get_active_profiles(skip=skip, limit=size)
    total = corporate_repo.count_active()

    # Add base URL to all profiles and convert to response format
    profiles_with_urls = [add_base_url_to_profile(profile) for profile in profiles]
    profiles_response = [convert_profile_to_response(profile) for profile in profiles_with_urls]

    return CorporateProfileListResponse(
        corporate_profiles=profiles_response,
        total=total,
        page=page,
        size=size
    )


@router.get("/{profile_id}", response_model=CorporateProfileResponse, tags=["Corporate Profile"])
async def get_corporate_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    """Get corporate profile by ID"""
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(profile_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    profile_with_urls = add_base_url_to_profile(profile)
    return convert_profile_to_response(profile_with_urls)


@router.get("/user/me", response_model=CorporateProfileResponse, tags=["Corporate Profile"])
async def get_my_corporate_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's corporate profile"""
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_user_id(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    profile_with_urls = add_base_url_to_profile(profile)
    return convert_profile_to_response(profile_with_urls)


@router.put("/{profile_id}", response_model=CorporateProfileResponse, tags=["Corporate Profile"])
async def update_corporate_profile(
    profile_id: int,
    company_name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    country_code: Optional[str] = Form(None),
    location_id: Optional[int] = Form(None),
    overview: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    company_size: Optional[CompanySize] = Form(None),
    logo: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update corporate profile with logo upload"""
    from ..models.location import Location
    
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if profile exists and belongs to current user
    profile = corporate_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )
    
    # Validate location if provided
    if location_id is not None:
        location = db.query(Location).filter(Location.id == location_id, Location.is_deleted == False).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid location ID"
            )
    
    # Validate logo file if provided
    if logo and not logo.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed for logo"
        )
    
    # Prepare update data
    update_data = CorporateProfileUpdate()
    if company_name is not None:
        update_data.company_name = company_name
    if industry is not None:
        update_data.industry = industry
    if phone_number is not None:
        update_data.phone_number = phone_number
    if country_code is not None:
        update_data.country_code = country_code
    if location_id is not None:
        update_data.location_id = location_id
    if overview is not None:
        update_data.overview = overview
    if website_url is not None:
        update_data.website_url = website_url
    if company_size is not None:
        update_data.company_size = company_size
    
    # Update profile
    updated_profile = corporate_repo.update(profile_id, update_data)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    # Handle logo upload if provided
    if logo:
        try:
            logo_url = save_logo_file(logo, profile_id)
            # Update profile with new logo URL
            updated_profile.logo_url = logo_url
            db.commit()
            db.refresh(updated_profile)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload logo: {str(e)}"
            )
    
    # Get the updated profile with relationships
    updated_profile_with_relations = corporate_repo.get_by_id(profile_id)
    profile_with_urls = add_base_url_to_profile(updated_profile_with_relations)
    
    return convert_profile_to_response(profile_with_urls)


@router.delete("/{profile_id}", response_model=MessageResponse, tags=["Corporate Profile"])
async def delete_corporate_profile(
    profile_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete corporate profile"""
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if profile exists and belongs to current user
    profile = corporate_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this profile"
        )
    
    success = corporate_repo.delete(profile_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile"
        )
    
    return MessageResponse(message="Corporate profile deleted successfully")


@router.post("/verify", response_model=MessageResponse, tags=["Corporate Profile"])
async def verify_corporate_profile(
    verification: CorporateProfileVerification,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify corporate profile with OTP"""
    # Find valid OTP
    otp = db.query(OTP).filter(
        OTP.email == current_user.email,
        OTP.otp_code == verification.otp_code,
        OTP.otp_type == "corporate_verification",
        OTP.is_used == False
    ).first()
    
    if not otp or otp.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Get profile ID from OTP data
    profile_data = otp.get_data()
    profile_id = profile_data.get("profile_id")
    
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP data"
        )
    
    # Verify profile
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.verify_profile(profile_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    # Mark OTP as used
    otp.is_used = True
    db.commit()
    
    return MessageResponse(message="Corporate profile verified successfully")
