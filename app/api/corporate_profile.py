from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path
from ..db.database import get_db
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
from ..utils.permissions import check_admin_or_owner, is_admin_user
from ..utils.email import send_email_with_retry, send_corporate_verification_email
from ..core.config import settings
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


def generate_otp(email: Optional[str] = None) -> str:
    """Generate 6-digit OTP. Returns '1234' for test user (example@phix.com)"""
    if email and email.lower() == "example@phix.com":
        return "1234"
    return ''.join(random.choices(string.digits, k=6))




async def save_logo_file(logo_file: UploadFile, profile_id: int) -> str:
    """Save logo file and return the URL"""
    project_root = Path(__file__).parent.parent.parent
    
    upload_dir = project_root / "static" / "logos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_extension = logo_file.filename.split('.')[-1] if logo_file.filename else 'jpg'
    unique_filename = f"logo_{profile_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    try:
        content = await logo_file.read()
        with open(file_path, "wb") as buffer:
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
    
    return f"/static/logos/{unique_filename}"


def add_base_url_to_profile(profile):
    """Add base URL to logo_url, location.flag_image, user.avatar_url, and team member avatars"""
    try:
        print(f"[DEBUG] add_base_url_to_profile: profile_id={getattr(profile, 'id', 'unknown')}")
        if hasattr(profile, 'logo_url') and profile.logo_url:
            print(f"[DEBUG] Adding base URL to logo: {profile.logo_url}")
            profile.logo_url = f"{settings.BASE_URL}{profile.logo_url}"
        
        if hasattr(profile, 'location') and profile.location and hasattr(profile.location, 'flag_image') and profile.location.flag_image:
            profile.location.flag_image = f"{settings.BASE_URL}{profile.location.flag_image}"
        
        if hasattr(profile, 'user') and profile.user and hasattr(profile.user, 'avatar_url') and profile.user.avatar_url:
            profile.user.avatar_url = f"{settings.BASE_URL}{profile.user.avatar_url}"
        
        if hasattr(profile, 'team_members') and profile.team_members:
            for team_member in profile.team_members:
                if team_member.user and hasattr(team_member.user, 'avatar_url') and team_member.user.avatar_url:
                    team_member.user.avatar_url = f"{settings.BASE_URL}{team_member.user.avatar_url}"
        
        return profile
    except Exception as e:
        import traceback
        error_msg = f"Error adding base URL to profile: {str(e)}"
        print(f"ERROR in add_base_url_to_profile: {error_msg}")
        print(traceback.format_exc())
        return profile


def convert_profile_to_response(profile_with_urls, current_user_id: Optional[int] = None, db: Optional[Session] = None):
    """Convert CorporateProfile model to CorporateProfileResponse format"""
    try:
        print(f"[DEBUG] Converting profile to response: profile_id={getattr(profile_with_urls, 'id', 'unknown')}")
        from ..schemas.corporate_profile import CorporateProfileResponse, TeamMemberResponse
        
        print(f"[DEBUG] Processing team members...")
        team_members_data = []
        if hasattr(profile_with_urls, 'team_members') and profile_with_urls.team_members:
            print(f"[DEBUG] Found {len(profile_with_urls.team_members)} team members")
            for team_member in profile_with_urls.team_members:
                try:
                    team_member_data = {
                        "id": team_member.id,
                        "user_id": team_member.user_id,
                        "user_name": team_member.user.name if team_member.user else "",
                        "user_email": team_member.user.email if team_member.user else "",
                        "user_avatar": team_member.user.avatar_url if team_member.user else None,
                        "role": team_member.role.value if hasattr(team_member.role, 'value') else str(team_member.role),
                        "status": team_member.status.value if hasattr(team_member.status, 'value') else str(team_member.status),
                        "invited_by_user_id": team_member.invited_by_user_id,
                        "invited_by_name": team_member.invited_by.name if team_member.invited_by else "",
                        "created_at": team_member.created_at,
                        "accepted_at": team_member.accepted_at,
                        "rejected_at": team_member.rejected_at
                    }
                    team_members_data.append(team_member_data)
                except Exception as e:
                    print(f"Error processing team member {getattr(team_member, 'id', 'unknown')}: {str(e)}")
                    continue
        
        is_followed = False
        follow_relation_id = None
        followers_count = 0
        # Corporate profile follow functionality disabled - table dropped in migration
        # if db:
        #     try:
        #         from ..repositories.corporate_profile_follow_repository import CorporateProfileFollowRepository
        #         follow_repo = CorporateProfileFollowRepository(db)
        #         
        #         followers_count = follow_repo.count_followers(profile_with_urls.id)
        #         
        #         if current_user_id is not None and profile_with_urls.id:
        #             from ..models.corporate_profile_follow import CorporateProfileFollow
        #             from sqlalchemy import and_
        #             follow_relation = db.query(CorporateProfileFollow).filter(
        #                 and_(
        #                     CorporateProfileFollow.user_id == int(current_user_id),
        #                     CorporateProfileFollow.corporate_profile_id == int(profile_with_urls.id)
        #                 )
        #             ).first()
        #             if follow_relation:
        #                 is_followed = True
        #                 follow_relation_id = int(follow_relation.id)
        #     except Exception as e:
        #         print(f"Error checking follow status: {str(e)}")
        
        print(f"[DEBUG] Processing company_size...")
        company_size_value = profile_with_urls.company_size.value if hasattr(profile_with_urls.company_size, 'value') else str(profile_with_urls.company_size)
        print(f"[DEBUG] company_size={company_size_value}")
        
        print(f"[DEBUG] Creating profile dict...")
        profile_dict = {
            "id": profile_with_urls.id,
            "company_name": getattr(profile_with_urls, "company_name", ""),
            "category_id": getattr(profile_with_urls, "category_id", None),
            "phone_number": getattr(profile_with_urls, "phone_number", ""),
            "country_code": getattr(profile_with_urls, "country_code", ""),
            "location_id": getattr(profile_with_urls, "location_id", None),
            "overview": getattr(profile_with_urls, "overview", ""),
            "website_url": getattr(profile_with_urls, "website_url", None),
            "company_size": company_size_value,
            "logo_url": getattr(profile_with_urls, "logo_url", None),
            "user_id": getattr(profile_with_urls, "user_id", None),
            "is_active": getattr(profile_with_urls, "is_active", False),
            "is_verified": getattr(profile_with_urls, "is_verified", False),
            "created_at": getattr(profile_with_urls, "created_at", None),
            "updated_at": getattr(profile_with_urls, "updated_at", None),
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
            "category": {
                "id": profile_with_urls.category.id,
                "name": profile_with_urls.category.name,
                "description": profile_with_urls.category.description,
                "is_active": profile_with_urls.category.is_active
            } if hasattr(profile_with_urls, 'category') and profile_with_urls.category else None,
            "team_members": team_members_data,
            "is_followed": is_followed,
            "followers_count": followers_count,
            "follow_relation_id": follow_relation_id
        }
        
        print(f"[DEBUG] Creating CorporateProfileResponse from dict...")
        response = CorporateProfileResponse(**profile_dict)
        print(f"[DEBUG] CorporateProfileResponse created successfully")
        return response
    except Exception as e:
        import traceback
        error_msg = f"Error converting profile to response: {str(e)}"
        print(f"ERROR in convert_profile_to_response: {error_msg}")
        print(traceback.format_exc())
        raise


@router.post("/", response_model=SuccessResponse, tags=["Corporate Profile"])
async def create_corporate_profile(
    company_name: str = Form(...),
    phone_number: str = Form(...),
    country_code: str = Form(default="+1"),
    location_id: int = Form(...),
    overview: str = Form(...),
    website_url: Optional[str] = Form(None),
    company_size: CompanySize = Form(...),
    category_id: Optional[int] = Form(None),
    logo: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new corporate profile with logo upload"""
    try:
        print(f"[DEBUG] Creating corporate profile for user: {current_user.id} ({current_user.email})")
        print(f"[DEBUG] company_name={company_name}, location_id={location_id}, category_id={category_id}")
        
        from ..models.location import Location
        from ..models.category import Category
        
        # Handle logo - check if it's a valid file (not empty string or None)
        if logo:
            # Check if logo is actually a valid file with filename
            if not hasattr(logo, 'filename') or not logo.filename or not logo.filename.strip():
                # If logo is sent but has no filename (empty string case), treat it as None
                logo = None
        
        print(f"[DEBUG] Logo file: {logo.filename if logo else 'None'}")
        
        user_repo = UserRepository(db)
        corporate_repo = CorporateProfileRepository(db)
        
        print(f"[DEBUG] Checking if user has existing profile...")
        if corporate_repo.check_user_has_profile(current_user.id):
            print(f"[DEBUG] User already has profile - raising error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a corporate profile"
            )
        
        print(f"[DEBUG] User has no profile, proceeding...")
    
        print(f"[DEBUG] Validating location_id={location_id}")
        location = db.query(Location).filter(Location.id == location_id, Location.is_deleted == False).first()
        if not location:
            print(f"[DEBUG] Location not found: {location_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid location ID"
            )
        print(f"[DEBUG] Location found: {location.name}")
        
        if category_id is not None:
            print(f"[DEBUG] Validating category_id={category_id}")
            category_obj = db.query(Category).filter(
                Category.id == category_id,
                Category.is_active == True
            ).first()
            if not category_obj:
                print(f"[DEBUG] Category not found: {category_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid category ID"
                )
            print(f"[DEBUG] Category found: {category_obj.name}")
        
        logo_url = None
        if logo:
            # Validate logo is an image file
            if not logo.content_type or not logo.content_type.startswith('image/'):
                print(f"[DEBUG] Invalid logo content type: {logo.content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only image files are allowed for logo"
                )
            print(f"[DEBUG] Logo validated: {logo.content_type}")
        
        print(f"[DEBUG] Creating profile data object...")
        profile_data = CorporateProfileCreate(
            company_name=company_name,
            phone_number=phone_number,
            country_code=country_code,
            location_id=location_id,
            overview=overview,
            website_url=website_url,
            company_size=company_size,
            logo_url=None,
            category_id=category_id,
        )
        
        print(f"[DEBUG] Saving profile to database...")
        db_profile = corporate_repo.create(profile_data, current_user.id)
        print(f"[DEBUG] Profile created with ID: {db_profile.id}")
    
        if logo:
            try:
                print(f"[DEBUG] Uploading logo file...")
                logo_url = await save_logo_file(logo, db_profile.id)
                print(f"[DEBUG] Logo uploaded successfully: {logo_url}")
                db_profile.logo_url = logo_url
                db.commit()
                print(f"[DEBUG] Logo URL saved to database")
            except Exception as e:
                print(f"[DEBUG] Error uploading logo: {str(e)}")
                import traceback
                print(traceback.format_exc())
                db.delete(db_profile)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload logo: {str(e)}"
            )
    
        print(f"[DEBUG] Generating OTP for corporate verification...")
        otp_code = generate_otp(email=current_user.email)
        print(f"[DEBUG] OTP generated: {otp_code}")
        otp = OTP.create_otp(
            email=current_user.email,
            otp_code=otp_code,
            otp_type="corporate_verification",
            data={"profile_id": db_profile.id}
        )
        
        db.add(otp)
        db.commit()
        print(f"[DEBUG] OTP saved to database")
        
        try:
            print(f"[DEBUG] Creating owner team member...")
            from ..repositories.team_member_repository import TeamMemberRepository
            team_repo = TeamMemberRepository(db)
            team_repo.create_owner_member(
                corporate_profile_id=db_profile.id,
                user_id=current_user.id
            )
            print(f"[DEBUG] Owner team member created successfully")
        except Exception as e:
            print(f"[DEBUG] Failed to create owner team member: {e}")
            import traceback
            print(traceback.format_exc())
        
        try:
            print(f"[DEBUG] Sending verification email...")
            await send_corporate_verification_email(
                email=current_user.email,
                otp_code=otp_code
            )
            print(f"[DEBUG] Verification email sent successfully")
        except Exception as e:
            print(f"[DEBUG] Failed to send corporate verification email: {e}")
            import traceback
            print(traceback.format_exc())
        
        print(f"[DEBUG] Fetching updated profile...")
        updated_profile = corporate_repo.get_by_id(db_profile.id)
        print(f"[DEBUG] Converting profile to response...")
        profile_with_urls = add_base_url_to_profile(updated_profile)
        profile_response = convert_profile_to_response(profile_with_urls, current_user.id, db)
        
        print(f"[DEBUG] Corporate profile created successfully!")
        return SuccessResponse(
            msg="Corporate profile created successfully. Please check your email for verification code.",
            data=profile_response
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] UNEXPECTED ERROR in create_corporate_profile: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating corporate profile: {str(e)}"
        )




@router.get("/", response_model=CorporateProfileListResponse, tags=["Corporate Profile"])
async def get_corporate_profiles(
    page: int = 1,
    size: int = 10,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get all verified corporate profiles with pagination. Admin can see all profiles including unverified."""
    try:
        corporate_repo = CorporateProfileRepository(db)
        skip = (page - 1) * size

        is_admin = current_user and is_admin_user(current_user.get("email", ""))
        
        if is_admin:
            profiles = corporate_repo.get_all_profiles(skip=skip, limit=size)
            total = corporate_repo.count_all()
        else:
            profiles = corporate_repo.get_verified_profiles(skip=skip, limit=size)
            total = corporate_repo.count_verified()

        profiles_with_urls = [add_base_url_to_profile(profile) for profile in profiles]
        current_user_id = current_user.get("id") if current_user else None
        profiles_response = [convert_profile_to_response(profile, current_user_id, db) for profile in profiles_with_urls]

        return CorporateProfileListResponse(
            corporate_profiles=profiles_response,
            total=total,
            page=page,
            size=size
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error getting corporate profiles: {str(e)}"
        print(f"ERROR in get_corporate_profiles: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
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
    """Get corporate profile by ID (excludes deleted profiles)"""
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(profile_id, include_deleted=False)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    profile_with_urls = add_base_url_to_profile(profile)
    current_user_id = None
    if current_user:
        if isinstance(current_user, dict) and "id" in current_user:
            current_user_id = int(current_user["id"])
        elif hasattr(current_user, "id"):
            current_user_id = int(current_user.id)
    
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
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(profile_id, include_deleted=False)
    
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
    
    job_repo = FullTimeJobRepository(db)
    current_user_id = current_user.get("id") if current_user else None
    skip = (page - 1) * size
    
    jobs = job_repo.get_by_company_id(
        company_id=profile_id,
        skip=skip,
        limit=size,
        current_user_id=current_user_id,
        status="ACTIVE"
    )
    
    from ..models.full_time_job import FullTimeJob, JobStatus
    total = db.query(FullTimeJob).filter(
        FullTimeJob.company_id == profile_id,
        FullTimeJob.status == JobStatus.ACTIVE
    ).count()
    
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
    phone_number: Optional[str] = Form(None),
    country_code: Optional[str] = Form(None),
    location_id: Optional[int] = Form(None),
    overview: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    company_size: Optional[CompanySize] = Form(None),
    category_id: Optional[int] = Form(None),
    logo: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update corporate profile with logo upload"""
    from ..models.location import Location
    from ..models.category import Category
    
    # Handle logo - check if it's a valid file (not empty string or None)
    if logo:
        # Check if logo is actually a valid file with filename
        if not hasattr(logo, 'filename') or not logo.filename or not logo.filename.strip():
            # If logo is sent but has no filename (empty string case), treat it as None
            logo = None
    
    corporate_repo = CorporateProfileRepository(db)
    
    profile = corporate_repo.get_by_id(profile_id, include_deleted=False)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    if not check_admin_or_owner(current_user.email, current_user.id, profile.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )
    
    if location_id is not None:
        location = db.query(Location).filter(Location.id == location_id, Location.is_deleted == False).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid location ID"
            )
    
    if category_id is not None:
        category_obj = db.query(Category).filter(
            Category.id == category_id,
            Category.is_active == True
        ).first()
        if not category_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID"
            )
    
    if logo:
        # Validate logo is an image file
        if not logo.content_type or not logo.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed for logo"
            )
    
    update_data = CorporateProfileUpdate()
    if company_name is not None:
        update_data.company_name = company_name
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
    if category_id is not None:
        update_data.category_id = category_id
    
    updated_profile = corporate_repo.update(profile_id, update_data)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    if logo:
        try:
            logo_url = await save_logo_file(logo, profile_id)
            updated_profile.logo_url = logo_url
            db.commit()
            db.refresh(updated_profile)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload logo: {str(e)}"
            )
    
    updated_profile_with_relations = corporate_repo.get_by_id(profile_id, include_deleted=False)
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
    
    profile = corporate_repo.get_by_id(profile_id, include_deleted=True)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    if profile.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate profile is already deleted"
        )
    
    if not check_admin_or_owner(current_user.email, current_user.id, profile.user_id):
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
    
    profile = corporate_repo.get_by_user_id(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found for this user"
        )
    
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: This corporate profile does not belong to you"
        )
    
    if profile.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate profile is already verified"
        )
    
    existing_otp = db.query(OTP).filter(
        OTP.email == current_user.email,
        OTP.otp_type == "corporate_verification",
        OTP.is_used == False
    ).order_by(OTP.created_at.desc()).first()
    
    if existing_otp and not existing_otp.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid OTP code has already been sent. Please check your email or wait for the current code to expire before requesting a new one."
        )
    
    otp_code = generate_otp(email=current_user.email)
    otp = OTP.create_otp(
        email=current_user.email,
        otp_code=otp_code,
        otp_type="corporate_verification",
        data={"profile_id": profile.id}
    )
    
    db.add(otp)
    db.commit()
    
    try:
        await send_corporate_verification_email(
            email=current_user.email,
            otp_code=otp_code
        )
    except Exception as e:
        print(f"Failed to send corporate verification email: {e}")
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
    
    profile_data = otp.get_data()
    profile_id = profile_data.get("profile_id")
    
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP data"
        )
    
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(profile_id, include_deleted=False)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: This OTP is not for your corporate profile"
        )
    
    verified_profile = corporate_repo.verify_profile(profile_id)
    
    if not verified_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    otp.is_used = True
    db.commit()
    
    return MessageResponse(message="Corporate profile verified successfully")
