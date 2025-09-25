from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.repositories.team_member_repository import TeamMemberRepository
from app.repositories.corporate_profile_repository import CorporateProfileRepository
from app.schemas.team_member import (
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamMemberListResponse,
    UserSearchResponse,
    InvitationResponse,
    StatusUpdateRequest
)
from app.schemas.common import SuccessResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.team_member import TeamMemberStatus
from app.utils.email import send_team_invitation_email_new
from app.models.corporate_profile import CorporateProfile

router = APIRouter(prefix="/team-members", tags=["Team Members"])


@router.get("/search-users", response_model=List[UserSearchResponse])
async def search_users(
    query: str = Query(..., min_length=1, description="Search by name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search users by name or email"""
    from sqlalchemy import and_, or_
    
    # Simple user search without corporate profile filtering
    users = db.query(User).filter(
        and_(
            or_(
                User.name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            ),
            User.is_active == True,
            User.is_deleted == False,
            User.id != current_user.id  # Exclude current user
        )
    ).offset(skip).limit(limit).all()
    
    return [
        UserSearchResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            current_position=user.current_position
        )
        for user in users
    ]


@router.post("/invite", response_model=SuccessResponse)
async def invite_team_member(
    team_member: TeamMemberCreate,
    corporate_profile_id: int = Query(..., description="Corporate profile ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invite a new team member to the company"""
    # Verify user has access to this corporate profile
    corporate_profile_repo = CorporateProfileRepository(db)
    corporate_profile = corporate_profile_repo.get_by_id(corporate_profile_id)
    
    if not corporate_profile:
        raise HTTPException(status_code=404, detail="Corporate profile not found")
    
    if corporate_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    team_member_repo = TeamMemberRepository(db)
    
    try:
        new_team_member = team_member_repo.create_team_member(
            team_member, corporate_profile_id, current_user.id
        )
        
        # Send invitation email with team member ID
        await send_team_invitation_email_new(
            email=team_member.email,
            company_name=corporate_profile.company_name,
            inviter_name=current_user.name,
            role=team_member.role.value,
            team_member_id=new_team_member.id
        )
        
        return SuccessResponse(
            msg="Invitation sent successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=TeamMemberListResponse)
async def get_team_members(
    corporate_profile_id: int = Query(..., description="Corporate profile ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all team members for a corporate profile"""
    # Verify user has access to this corporate profile
    corporate_profile_repo = CorporateProfileRepository(db)
    corporate_profile = corporate_profile_repo.get_by_id(corporate_profile_id)
    
    if not corporate_profile:
        raise HTTPException(status_code=404, detail="Corporate profile not found")
    
    if corporate_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    team_member_repo = TeamMemberRepository(db)
    team_members = team_member_repo.get_team_members(corporate_profile_id, skip, limit)
    total = team_member_repo.get_team_member_count(corporate_profile_id)
    
    # Convert to response format
    team_member_responses = []
    for member in team_members:
        # Get user details
        user = db.query(User).filter(User.id == member.user_id).first()
        invited_by_user = db.query(User).filter(User.id == member.invited_by_user_id).first()
        
        if user and invited_by_user:
            team_member_responses.append(
                TeamMemberResponse(
                    id=member.id,
                    user_id=member.user_id,
                    user_name=user.name,
                    user_email=user.email,
                    user_avatar=user.avatar_url,
                    role=member.role,
                    status=member.status,
                    invited_by_user_id=member.invited_by_user_id,
                    invited_by_name=invited_by_user.name,
                    created_at=member.created_at,
                    accepted_at=member.accepted_at,
                    rejected_at=member.rejected_at
                )
            )
    
    return TeamMemberListResponse(
        team_members=team_member_responses,
        total=total
    )


@router.put("/{team_member_id}/role", response_model=TeamMemberResponse)
async def update_team_member_role(
    team_member_id: int,
    role_update: TeamMemberUpdate,
    corporate_profile_id: int = Query(..., description="Corporate profile ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update team member role"""
    # Verify user has access to this corporate profile
    corporate_profile_repo = CorporateProfileRepository(db)
    corporate_profile = corporate_profile_repo.get_by_id(corporate_profile_id)
    
    if not corporate_profile:
        raise HTTPException(status_code=404, detail="Corporate profile not found")
    
    if corporate_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    team_member_repo = TeamMemberRepository(db)
    updated_member = team_member_repo.update_team_member_role(team_member_id, role_update)
    
    if not updated_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    # Get user details for response
    user = db.query(User).filter(User.id == updated_member.user_id).first()
    invited_by_user = db.query(User).filter(User.id == updated_member.invited_by_user_id).first()
    
    if not user or not invited_by_user:
        raise HTTPException(status_code=500, detail="Error retrieving user information")
    
    return TeamMemberResponse(
        id=updated_member.id,
        user_id=updated_member.user_id,
        user_name=user.name,
        user_email=user.email,
        user_avatar=user.avatar_url,
        role=updated_member.role,
        status=updated_member.status,
        invited_by_user_id=updated_member.invited_by_user_id,
        invited_by_name=invited_by_user.name,
        created_at=updated_member.created_at,
        accepted_at=updated_member.accepted_at,
        rejected_at=updated_member.rejected_at
    )


@router.put("/{team_member_id}/status")
async def update_invitation_status(
    team_member_id: int,
    status_update: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update invitation status (accept/reject)"""
    team_member_repo = TeamMemberRepository(db)
    team_member = team_member_repo.get_team_member_by_id(team_member_id)
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member invitation not found")
    
    if team_member.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if team_member.status != TeamMemberStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation has already been processed")
    
    updated_member = team_member_repo.update_team_member_status(team_member_id, status_update.status)
    
    if not updated_member:
        raise HTTPException(status_code=500, detail="Error updating invitation status")
    
    status_text = "accepted" if status_update.status else "rejected"
    return SuccessResponse(
        msg=f"Invitation {status_text} successfully"
    )


@router.delete("/{team_member_id}")
async def remove_team_member(
    team_member_id: int,
    corporate_profile_id: int = Query(..., description="Corporate profile ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove team member from company"""
    # Verify user has access to this corporate profile
    corporate_profile_repo = CorporateProfileRepository(db)
    corporate_profile = corporate_profile_repo.get_by_id(corporate_profile_id)
    
    if not corporate_profile:
        raise HTTPException(status_code=404, detail="Corporate profile not found")
    
    if corporate_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    team_member_repo = TeamMemberRepository(db)
    success = team_member_repo.remove_team_member(team_member_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    return SuccessResponse(
        msg="Team member removed successfully"
    )


@router.get("/pending-invitations", response_model=List[TeamMemberResponse])
async def get_pending_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending invitations for the current user"""
    team_member_repo = TeamMemberRepository(db)
    pending_invitations = team_member_repo.get_pending_invitations(current_user.id)
    
    # Convert to response format
    invitation_responses = []
    for invitation in pending_invitations:
        # Get company and inviter details
        corporate_profile = db.query(CorporateProfile).filter(
            CorporateProfile.id == invitation.corporate_profile_id
        ).first()
        inviter_user = db.query(User).filter(User.id == invitation.invited_by_user_id).first()
        
        if corporate_profile and inviter_user:
            invitation_responses.append(
                TeamMemberResponse(
                    id=invitation.id,
                    user_id=invitation.user_id,
                    user_name=current_user.name,
                    user_email=current_user.email,
                    user_avatar=current_user.avatar_url,
                    role=invitation.role,
                    status=invitation.status,
                    invited_by_user_id=invitation.invited_by_user_id,
                    invited_by_name=inviter_user.name,
                    created_at=invitation.created_at,
                    accepted_at=invitation.accepted_at,
                    rejected_at=invitation.rejected_at
                )
            )
    
    return invitation_responses


@router.get("/accept-invitation")
async def accept_invitation(
    team_member_id: int = Query(..., description="Team member invitation ID"),
    db: Session = Depends(get_db)
):
    """Accept team member invitation (no authentication required)"""
    team_member_repo = TeamMemberRepository(db)
    team_member = team_member_repo.get_team_member_by_id(team_member_id)
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member invitation not found")
    
    if team_member.status != TeamMemberStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation has already been processed")
    
    # Accept the invitation
    updated_member = team_member_repo.update_team_member_status(team_member_id, True)
    
    if not updated_member:
        raise HTTPException(status_code=500, detail="Error accepting invitation")
    
    # Return HTML response for better user experience
    html_response = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Invitation Accepted</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #4CAF50; font-size: 24px; margin-bottom: 20px; }
            .message { color: #333; font-size: 16px; margin-bottom: 30px; }
            .button { display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅ Invitation Accepted!</div>
            <div class="message">You have successfully accepted the team invitation. You can now close this window.</div>
            <a href="#" onclick="window.close()" class="button">Close Window</a>
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_response)


@router.get("/reject-invitation")
async def reject_invitation(
    team_member_id: int = Query(..., description="Team member invitation ID"),
    db: Session = Depends(get_db)
):
    """Reject team member invitation (no authentication required)"""
    team_member_repo = TeamMemberRepository(db)
    team_member = team_member_repo.get_team_member_by_id(team_member_id)
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member invitation not found")
    
    if team_member.status != TeamMemberStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation has already been processed")
    
    # Reject the invitation
    updated_member = team_member_repo.update_team_member_status(team_member_id, False)
    
    if not updated_member:
        raise HTTPException(status_code=500, detail="Error rejecting invitation")
    
    # Return HTML response for better user experience
    html_response = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Invitation Rejected</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .rejected { color: #f44336; font-size: 24px; margin-bottom: 20px; }
            .message { color: #333; font-size: 16px; margin-bottom: 30px; }
            .button { display: inline-block; padding: 12px 24px; background-color: #f44336; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="rejected">❌ Invitation Rejected</div>
            <div class="message">You have declined the team invitation. You can now close this window.</div>
            <a href="#" onclick="window.close()" class="button">Close Window</a>
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_response)