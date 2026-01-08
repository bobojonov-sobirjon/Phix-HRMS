"""
Admin API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Body, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from ..db.database import get_db
from ..repositories.user_repository import UserRepository
from ..schemas.common import SuccessResponse
from ..schemas.profile import UserFullResponse
from ..utils.decorators import handle_errors
from ..utils.response_helpers import success_response, not_found_error, forbidden_error
from ..models.user import User
from ..models.gig_job import GigJob
from ..models.full_time_job import FullTimeJob
from ..models.proposal import Proposal
from ..models.saved_job import SavedJob
from ..models.corporate_profile import CorporateProfile
from ..api.auth import get_current_user
from ..pagination import PaginationParams, create_pagination_response

router = APIRouter(prefix="/admin", tags=["Admin"])


def check_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """Check if current user has admin role"""
    role_names = [role.name.lower() for role in current_user.roles]
    if "admin" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class BlockUserRequest(BaseModel):
    """Request model for blocking a user"""
    reason: Optional[str] = None


class UserAdminResponse(UserFullResponse):
    """User response for admin with additional statistics"""
    is_deleted: bool
    blocked_at: Optional[datetime] = None
    block_reason: Optional[str] = None
    blocked_by: Optional[int] = None
    gig_jobs_count: int = 0
    full_time_jobs_count: int = 0
    proposals_count: int = 0
    saved_jobs_count: int = 0
    has_corporate_profile: bool = False
    
    class Config:
        from_attributes = True


@router.get("/users", response_model=SuccessResponse, tags=["Admin"])
@handle_errors
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role (employer/worker)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    is_deleted: Optional[bool] = Query(None, description="Filter by deleted status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    date_from: Optional[datetime] = Query(None, description="Filter by registration date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by registration date to"),
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db)
):
    """
    Get all users with filters and pagination (Admin only)
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **role**: Filter by role (employer/worker)
    - **is_active**: Filter by active status
    - **is_verified**: Filter by verification status
    - **is_deleted**: Filter by deleted status
    - **search**: Search by name or email
    - **date_from**: Filter by registration date from
    - **date_to**: Filter by registration date to
    """
    user_repo = UserRepository(db)
    skip = (page - 1) * limit
    
    users, total = user_repo.get_all_users_with_filters(
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        is_deleted=is_deleted,
        search=search,
        date_from=date_from,
        date_to=date_to
    )
    
    users_data = []
    for user in users:
        gig_jobs_count = db.query(GigJob).filter(
            GigJob.author_id == user.id,
            GigJob.is_deleted == False
        ).count()
        
        full_time_jobs_count = 0
        corporate_profile = db.query(CorporateProfile).filter(
            CorporateProfile.user_id == user.id,
            CorporateProfile.is_deleted == False
        ).first()
        if corporate_profile:
            full_time_jobs_count = db.query(FullTimeJob).filter(
                FullTimeJob.company_id == corporate_profile.id
            ).count()
        
        proposals_count = db.query(Proposal).filter(
            Proposal.user_id == user.id,
            Proposal.is_deleted == False
        ).count()
        
        saved_jobs_count = db.query(SavedJob).filter(
            SavedJob.user_id == user.id
        ).count()
        
        has_corporate_profile = corporate_profile is not None
        
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_social_user": user.is_social_user,
            "is_deleted": user.is_deleted,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "about_me": user.about_me,
            "current_position": user.current_position,
            "location_id": user.location_id,
            "main_category_id": user.main_category_id,
            "sub_category_id": user.sub_category_id,
            "language_id": user.language_id,
            "blocked_at": user.blocked_at,
            "block_reason": user.block_reason,
            "blocked_by": user.blocked_by,
            "gig_jobs_count": gig_jobs_count,
            "full_time_jobs_count": full_time_jobs_count,
            "proposals_count": proposals_count,
            "saved_jobs_count": saved_jobs_count,
            "has_corporate_profile": has_corporate_profile,
            "roles": [{"id": role.id, "name": role.name} for role in user.roles],
            "location": {
                "id": user.location.id,
                "name": user.location.name,
                "code": user.location.code,
                "phone_code": user.location.phone_code,
                "flag_image": user.location.flag_image
            } if user.location else None,
            "language": {
                "id": user.language.id,
                "name": user.language.name
            } if user.language else None,
            "main_category": {
                "id": user.main_category.id,
                "name": user.main_category.name,
                "description": user.main_category.description,
                "is_active": user.main_category.is_active
            } if user.main_category else None,
            "sub_category": {
                "id": user.sub_category.id,
                "name": user.sub_category.name,
                "description": user.sub_category.description,
                "is_active": user.sub_category.is_active
            } if user.sub_category else None,
            "skills": [{"id": skill.id, "name": skill.name} for skill in user.skills if not skill.is_deleted]
        }
        
        users_data.append(user_dict)
    
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return success_response(
        data={
            "users": users_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages
        },
        message="Users retrieved successfully"
    )


@router.patch("/users/{user_id}/block", response_model=SuccessResponse, tags=["Admin"])
@handle_errors
async def block_user(
    user_id: int,
    request: Optional[BlockUserRequest] = Body(None),
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db)
):
    """
    Block a user (set is_active to false)
    
    - **user_id**: ID of the user to block
    - **reason**: Optional reason for blocking
    """
    user_repo = UserRepository(db)
    
    target_user = user_repo.get_user_by_id_including_deleted(user_id)
    if not target_user:
        raise not_found_error("User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot block yourself"
        )
    
    if not target_user.is_active:
        return success_response(
            data={"user_id": user_id, "is_active": False},
            message="User is already blocked"
        )
    
    block_reason = request.reason if request and request.reason else None
    success = user_repo.block_user(user_id, current_user.id, block_reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block user"
        )
    
    return success_response(
        data={
            "user_id": user_id,
            "is_active": False,
            "blocked_at": target_user.blocked_at.isoformat() if target_user.blocked_at else None,
            "block_reason": target_user.block_reason
        },
        message="User blocked successfully"
    )


@router.patch("/users/{user_id}/unblock", response_model=SuccessResponse, tags=["Admin"])
@handle_errors
async def unblock_user(
    user_id: int,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db)
):
    """
    Unblock a user (set is_active to true)
    
    - **user_id**: ID of the user to unblock
    """
    user_repo = UserRepository(db)
    
    target_user = user_repo.get_user_by_id_including_deleted(user_id)
    if not target_user:
        raise not_found_error("User not found")
    
    if target_user.is_active:
        return success_response(
            data={"user_id": user_id, "is_active": True},
            message="User is already active"
        )
    
    success = user_repo.unblock_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock user"
        )
    
    return success_response(
        data={
            "user_id": user_id,
            "is_active": True
        },
        message="User unblocked successfully"
    )
