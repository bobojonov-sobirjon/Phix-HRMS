from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..repositories.corporate_profile_follow_repository import CorporateProfileFollowRepository
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..schemas.corporate_profile_follow import (
    CorporateProfileFollowCreate,
    CorporateProfileFollowResponse,
    CorporateProfileFollowDetailedResponse,
    CorporateProfileFollowerResponse,
    CorporateProfileFollowListResponse,
    CorporateProfileFollowerListResponse
)
from ..schemas.common import MessageResponse, SuccessResponse
from ..utils.auth import get_current_user
from ..pagination import PaginationParams, create_pagination_response
from ..config import settings
from ..schemas.corporate_profile import CorporateProfileResponse
from ..utils.firebase_notifications import send_push_notification_multiple
from ..models.user_device_token import UserDeviceToken


router = APIRouter(prefix="/corporate-profile-follow", tags=["Corporate Profile Follow"])


def get_user_device_tokens(db: Session, user_id: int) -> List[str]:
    """Get all active device tokens for a user"""
    device_tokens = db.query(UserDeviceToken).filter(
        UserDeviceToken.user_id == user_id,
        UserDeviceToken.is_active == True
    ).all()
    return [token.device_token for token in device_tokens if token.device_token]


def send_follow_notification(
    db: Session,
    recipient_user_id: int,
    follower_name: str,
    company_name: str,
    corporate_profile_id: int
):
    """Send push notification to corporate profile owner when someone follows"""
    try:
        device_tokens = get_user_device_tokens(db, recipient_user_id)
        
        if not device_tokens:
            return
        
        title = "New Follower"
        body = f"{follower_name} started following {company_name}"
        data = {
            "type": "corporate_profile_follow",
            "corporate_profile_id": str(corporate_profile_id),
            "follower_name": follower_name,
            "company_name": company_name
        }
        
        send_push_notification_multiple(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data={str(k): str(v) for k, v in data.items()}
        )
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"ERROR: Failed to send follow notification to user_id={recipient_user_id}: {str(e)}")


def add_base_url_to_profile(profile):
    """Add base URL to logo_url, location.flag_image, user.avatar_url, and team member avatars"""
    if profile.logo_url:
        profile.logo_url = f"{settings.BASE_URL}{profile.logo_url}" if not profile.logo_url.startswith('http') else profile.logo_url
    
    if profile.location and profile.location.flag_image:
        profile.location.flag_image = f"{settings.BASE_URL}{profile.location.flag_image}" if not profile.location.flag_image.startswith('http') else profile.location.flag_image
    
    if profile.user and profile.user.avatar_url:
        profile.user.avatar_url = f"{settings.BASE_URL}{profile.user.avatar_url}" if not profile.user.avatar_url.startswith('http') else profile.user.avatar_url
    
    # Add base URL to team member avatars
    if hasattr(profile, 'team_members') and profile.team_members:
        for team_member in profile.team_members:
            if team_member.user and team_member.user.avatar_url:
                team_member.user.avatar_url = f"{settings.BASE_URL}{team_member.user.avatar_url}" if not team_member.user.avatar_url.startswith('http') else team_member.user.avatar_url
    
    return profile


def convert_profile_to_response(profile_with_urls, current_user_id: Optional[int] = None, db: Optional[Session] = None):
    """Convert CorporateProfile model to CorporateProfileResponse format"""
    from ..schemas.corporate_profile import TeamMemberResponse
    
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
    if current_user_id and db:
        from ..repositories.corporate_profile_follow_repository import CorporateProfileFollowRepository
        follow_repo = CorporateProfileFollowRepository(db)
        is_followed = follow_repo.is_following(current_user_id, profile_with_urls.id)
    
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
        "is_followed": is_followed
    }
    
    return CorporateProfileResponse(**profile_dict)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse)
async def follow_corporate_profile(
    follow_data: CorporateProfileFollowCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Follow a corporate profile.
    
    - **corporate_profile_id**: ID of the corporate profile to follow
    - User ID is taken from the authentication token
    """
    try:
        repository = CorporateProfileFollowRepository(db)
        
        # Get corporate profile to get owner info
        corporate_repo = CorporateProfileRepository(db)
        corporate_profile = corporate_repo.get_by_id(follow_data.corporate_profile_id)
        
        if not corporate_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Corporate profile not found"
            )
        
        follow = repository.create(
            corporate_profile_id=follow_data.corporate_profile_id,
            user_id=current_user.id
        )
        
        # Send push notification to corporate profile owner
        if corporate_profile.user_id != current_user.id:  # Don't send notification if user follows their own profile
            send_follow_notification(
                db=db,
                recipient_user_id=corporate_profile.user_id,
                follower_name=current_user.name,
                company_name=corporate_profile.company_name,
                corporate_profile_id=corporate_profile.id
            )
        
        return SuccessResponse(
            msg="Successfully followed corporate profile",
            data=CorporateProfileFollowResponse.model_validate(follow)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to follow corporate profile: {str(e)}"
        )


@router.delete("/{follow_id}", response_model=MessageResponse)
async def unfollow_corporate_profile(
    follow_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unfollow a corporate profile.
    
    - **follow_id**: ID of the follow relationship to delete
    - User ID is taken from the authentication token
    """
    repository = CorporateProfileFollowRepository(db)
    success = repository.delete_by_id(
        follow_id=follow_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow relationship not found"
        )
    
    return MessageResponse(message="Successfully unfollowed corporate profile")


@router.get("/user-following", response_model=CorporateProfileFollowListResponse)
async def get_user_following(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all corporate profiles that the current user is following.
    
    Returns full corporate profile details with pagination.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = CorporateProfileFollowRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    follows, total = repository.get_user_following(current_user.id, pagination)
    
    # Convert follows to detailed response format
    follow_responses = []
    for follow in follows:
        if follow.corporate_profile:
            # Add base URL to profile
            profile_with_urls = add_base_url_to_profile(follow.corporate_profile)
            # Convert to response format
            corporate_profile_response = convert_profile_to_response(profile_with_urls, current_user.id, db)
            # Since this is from user-following API, user is definitely following, so set is_followed to True
            corporate_profile_response.is_followed = True
            
            follow_response = CorporateProfileFollowDetailedResponse(
                id=follow.id,
                corporate_profile=corporate_profile_response,
                created_at=follow.created_at
            )
            follow_responses.append(follow_response)
    
    paginated_response = create_pagination_response(
        items=follow_responses,
        total=total,
        pagination=pagination
    )
    
    return CorporateProfileFollowListResponse(
        items=paginated_response.items,
        total=paginated_response.total,
        page=paginated_response.page,
        size=paginated_response.size,
        pages=paginated_response.pages
    )


@router.get("/corporate-profile-followers/{corporate_profile_id}", response_model=CorporateProfileFollowerListResponse)
async def get_corporate_profile_followers(
    corporate_profile_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get all users who follow a specific corporate profile.
    
    Returns full user details with pagination.
    
    - **corporate_profile_id**: ID of the corporate profile
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    # Check if corporate profile exists
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(corporate_profile_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate profile not found"
        )
    
    repository = CorporateProfileFollowRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    follows, total = repository.get_corporate_profile_followers(corporate_profile_id, pagination)
    
    # Convert follows to detailed response format
    from ..schemas.profile import UserFullResponse
    from ..config import settings
    
    follower_responses = []
    for follow in follows:
        if follow.user:
            # Add base URL to user avatar if exists
            user_data = follow.user
            if user_data.avatar_url:
                user_data.avatar_url = f"{settings.BASE_URL}{user_data.avatar_url}" if not user_data.avatar_url.startswith('http') else user_data.avatar_url
            
            # Convert user to full response
            user_response = UserFullResponse.model_validate(user_data)
            
            follower_response = CorporateProfileFollowerResponse(
                id=follow.id,
                user=user_response,
                created_at=follow.created_at
            )
            follower_responses.append(follower_response)
    
    paginated_response = create_pagination_response(
        items=follower_responses,
        total=total,
        pagination=pagination
    )
    
    return CorporateProfileFollowerListResponse(
        items=paginated_response.items,
        total=paginated_response.total,
        page=paginated_response.page,
        size=paginated_response.size,
        pages=paginated_response.pages
    )

