from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
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
    CorporateProfileListResponse
)
from ..schemas.common import MessageResponse, SuccessResponse
from ..utils.auth import get_current_user
from ..utils.email import send_email_with_retry
from ..models.otp import OTP
import random
import string

router = APIRouter(prefix="/corporate-profile", tags=["Corporate Profile"])


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


@router.post("/", response_model=SuccessResponse, tags=["Corporate Profile"])
async def create_corporate_profile(
    corporate_profile: CorporateProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new corporate profile"""
    user_repo = UserRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if user already has a corporate profile
    if corporate_repo.check_user_has_profile(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a corporate profile"
        )
    
    # Create corporate profile
    db_profile = corporate_repo.create(corporate_profile, current_user.id)
    
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
    
    # Send verification email
    try:
        send_email_with_retry(
            email=current_user.email,
            otp_code=otp_code,
            email_type="corporate_verification"
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send verification email: {e}")
    
    return SuccessResponse(
        msg="Corporate profile created successfully. Please check your email for verification code.",
        data={"profile_id": db_profile.id}
    )


@router.post("/upload-logo", response_model=SuccessResponse, tags=["Corporate Profile"])
async def upload_corporate_logo(
    logo_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload logo for corporate profile"""
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if user has a corporate profile
    profile = corporate_repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate profile required to upload logo"
        )
    
    # Validate file type
    if not logo_file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("static/logos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = logo_file.filename.split('.')[-1]
    unique_filename = f"logo_{profile.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await logo_file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save logo: {str(e)}"
        )
    
    # Update profile with logo URL
    logo_url = f"/static/logos/{unique_filename}"
    profile.logo_url = logo_url
    db.commit()
    
    return SuccessResponse(
        msg="Logo uploaded successfully",
        data={"logo_url": logo_url}
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
    
    return CorporateProfileListResponse(
        corporate_profiles=profiles,
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
    
    return CorporateProfileListResponse(
        corporate_profiles=profiles,
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
    
    return profile


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
    
    return profile


@router.put("/{profile_id}", response_model=CorporateProfileResponse, tags=["Corporate Profile"])
async def update_corporate_profile(
    profile_id: int,
    corporate_profile: CorporateProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update corporate profile"""
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
    
    updated_profile = corporate_repo.update(profile_id, corporate_profile)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return updated_profile


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
