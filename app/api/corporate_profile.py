from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path
from ..database import get_db
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..repositories.user_repository import UserRepository
from ..repositories.full_time_job_repository import FullTimeJobRepository
from ..schemas.corporate_profile import (
    CorporateProfileCreate,
    CorporateProfileUpdate,
    CorporateProfileResponse,
    CorporateProfileVerification,
    CorporateProfileListResponse,
    CompanySize
)
from ..schemas.full_time_job import FullTimeJobResponse, FullTimeJobListResponse
from ..schemas.common import MessageResponse, SuccessResponse
from ..utils.auth import get_current_user, verify_token
from ..utils.email import send_email_with_retry, send_corporate_verification_email
from ..config import settings
from ..models.otp import OTP
from ..models.user import User
import random
import string

router = APIRouter(prefix="/corporate-profile", tags=["Corporate Profile"])


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """Get current user if authorization header is provided, otherwise return None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        payload = verify_token(token)
        if payload and 'sub' in payload:
            user_id = int(payload['sub'])
            user_repo = UserRepository(db)
            user = user_repo.get_user_by_id(user_id)
            if user:
                return {"id": user.id, "name": user.name, "email": user.email}
        return None
    except Exception:
        return None


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def save_logo_file(logo_file: UploadFile, profile_id: int) -> str:
    """Save logo file and return the URL"""
    # Get absolute path to project root (where app folder is)
    project_root = Path(__file__).parent.parent.parent
    
    # Create uploads directory if it doesn't exist
    upload_dir = project_root / "static" / "logos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = logo_file.filename.split('.')[-1] if logo_file.filename else 'jpg'
    unique_filename = f"logo_{profile_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = logo_file.file.read()
            buffer.write(content)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Permission denied when saving file. Please check directory permissions: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
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


def convert_profile_to_response(profile_with_urls, current_user_id: Optional[int] = None, db: Optional[Session] = None):
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
    
    # Check if current user is following this profile
    is_followed = False
    follow_relation_id = None
    followers_count = 0
    if db:
        from ..repositories.corporate_profile_follow_repository import CorporateProfileFollowRepository
        follow_repo = CorporateProfileFollowRepository(db)
        
        # Get followers count
        followers_count = follow_repo.count_followers(profile_with_urls.id)
        
        # Check if current user is following and get follow relation ID
        # If token is provided, get user.id and corporate_profile_id, then filter CorporateProfileFollow
        if current_user_id and profile_with_urls.id:
            from ..models.corporate_profile_follow import CorporateProfileFollow
            from sqlalchemy import and_
            # Filter CorporateProfileFollow by user_id and corporate_profile_id
            follow_relation = db.query(CorporateProfileFollow).filter(
                and_(
                    CorporateProfileFollow.user_id == current_user_id,
                    CorporateProfileFollow.corporate_profile_id == profile_with_urls.id
                )
            ).first()
            # If follow relation exists, get its id
            if follow_relation:
                is_followed = True
                follow_relation_id = follow_relation.id
    
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
        "team_members": team_members_data,
        "is_followed": is_followed,
        "followers_count": followers_count,
        "follow_relation_id": follow_relation_id
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
    
    # Get the updated profile with relationships for response
    updated_profile = corporate_repo.get_by_id(db_profile.id)
    profile_with_urls = add_base_url_to_profile(updated_profile)
    profile_response = convert_profile_to_response(profile_with_urls, current_user.id, db)

    return SuccessResponse(
        msg="Corporate profile created successfully. Please check your email for verification code.",
        data=profile_response
    )




@router.get("/", response_model=CorporateProfileListResponse, tags=["Corporate Profile"])
async def get_corporate_profiles(
    page: int = 1,
    size: int = 10,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get all verified corporate profiles with pagination"""
    corporate_repo = CorporateProfileRepository(db)
    skip = (page - 1) * size

    profiles = corporate_repo.get_verified_profiles(skip=skip, limit=size)
    total = corporate_repo.count_verified()

    # Add base URL to all profiles and convert to response format
    profiles_with_urls = [add_base_url_to_profile(profile) for profile in profiles]
    current_user_id = current_user.get("id") if current_user else None
    profiles_response = [convert_profile_to_response(profile, current_user_id, db) for profile in profiles_with_urls]

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
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get only active corporate profiles"""
    corporate_repo = CorporateProfileRepository(db)
    skip = (page - 1) * size

    profiles = corporate_repo.get_active_profiles(skip=skip, limit=size)
    total = corporate_repo.count_active()

    # Add base URL to all profiles and convert to response format
    profiles_with_urls = [add_base_url_to_profile(profile) for profile in profiles]
    current_user_id = current_user.get("id") if current_user else None
    profiles_response = [convert_profile_to_response(profile, current_user_id, db) for profile in profiles_with_urls]

    return CorporateProfileListResponse(
        corporate_profiles=profiles_response,
        total=total,
        page=page,
        size=size
    )


@router.get("/{profile_id}", response_model=CorporateProfileResponse, tags=["Corporate Profile"])
async def get_corporate_profile(
    profile_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
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
    # Get user.id from token if token is provided
    current_user_id = None
    if current_user and isinstance(current_user, dict) and "id" in current_user:
        current_user_id = current_user["id"]
    
    return convert_profile_to_response(profile_with_urls, current_user_id, db)


@router.get("/{profile_id}/recently-posted-jobs", response_model=FullTimeJobListResponse, tags=["Corporate Profile"])
async def get_recently_posted_jobs(
    profile_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Page size"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get recently posted full-time jobs for a company (corporate profile).
    Returns jobs ordered by created_at DESC (most recent first).
    Only returns ACTIVE jobs.
    """
    # Check if corporate profile exists
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(profile_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    if not profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile is not active"
        )
    
    # Get recently posted jobs for this company (only ACTIVE jobs)
    job_repo = FullTimeJobRepository(db)
    current_user_id = current_user.get("id") if current_user else None
    skip = (page - 1) * size
    
    # Get jobs ordered by created_at DESC (recently posted first), only ACTIVE
    jobs = job_repo.get_by_company_id(
        company_id=profile_id,
        skip=skip,
        limit=size,
        current_user_id=current_user_id,
        status="ACTIVE"
    )
    
    # Get total count of active jobs
    from ..models.full_time_job import FullTimeJob, JobStatus
    total = db.query(FullTimeJob).filter(
        FullTimeJob.company_id == profile_id,
        FullTimeJob.status == JobStatus.ACTIVE
    ).count()
    
    # Convert dict responses to FullTimeJobResponse objects
    response_jobs = []
    for job in jobs:
        response_data = FullTimeJobResponse(**job)
        response_jobs.append(response_data)
    
    return FullTimeJobListResponse(
        jobs=response_jobs,
        total=total,
        page=page,
        size=size
    )


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
    return convert_profile_to_response(profile_with_urls, current_user.id, db)


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
    
    return convert_profile_to_response(profile_with_urls, current_user.id, db)


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


@router.post("/resend-otp", response_model=SuccessResponse, tags=["Corporate Profile"])
async def resend_corporate_otp(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resend OTP code for corporate profile verification - only for the authenticated user's corporate profile"""
    corporate_repo = CorporateProfileRepository(db)
    
    # Get the user's corporate profile (filtered by current_user from token)
    profile = corporate_repo.get_by_user_id(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found for this user"
        )
    
    # Verify the profile belongs to the current user (double check)
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: This corporate profile does not belong to you"
        )
    
    # Check if profile is already verified
    if profile.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate profile is already verified"
        )
    
    # Check if there's a valid (non-expired and unused) OTP for this profile
    existing_otp = db.query(OTP).filter(
        OTP.email == current_user.email,
        OTP.otp_type == "corporate_verification",
        OTP.is_used == False
    ).order_by(OTP.created_at.desc()).first()
    
    # Only generate new OTP if:
    # 1. No OTP exists, OR
    # 2. The existing OTP has expired
    if existing_otp and not existing_otp.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid OTP code has already been sent. Please check your email or wait for the current code to expire before requesting a new one."
        )
    
    # Generate new OTP
    otp_code = generate_otp()
    otp = OTP.create_otp(
        email=current_user.email,
        otp_code=otp_code,
        otp_type="corporate_verification",
        data={"profile_id": profile.id}
    )
    
    db.add(otp)
    db.commit()
    
    # Send verification email
    try:
        await send_corporate_verification_email(
            email=current_user.email,
            otp_code=otp_code
        )
    except Exception as e:
        print(f"Failed to send corporate verification email: {e}")
        # Return OTP in response for testing/development
        return SuccessResponse(
            msg="OTP code generated (email failed to send, check console for OTP)",
            data={"otp_code": otp_code}
        )
    
    return SuccessResponse(
        msg="OTP code resent successfully",
        data={
            "email": current_user.email,
            "profile_id": profile.id
        }
    )


@router.post("/verify", response_model=MessageResponse, tags=["Corporate Profile"])
async def verify_corporate_profile(
    verification: CorporateProfileVerification,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify corporate profile with OTP - only for the authenticated user's corporate profile"""
    # Find valid OTP for this user
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
    
    # Get the profile and verify it belongs to the current user
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(profile_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    # Verify the profile belongs to the current user
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: This OTP is not for your corporate profile"
        )
    
    # Verify profile
    verified_profile = corporate_repo.verify_profile(profile_id)
    
    if not verified_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    # Mark OTP as used
    otp.is_used = True
    db.commit()
    
    return MessageResponse(message="Corporate profile verified successfully")
