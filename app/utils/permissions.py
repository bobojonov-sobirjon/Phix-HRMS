from enum import Enum
from typing import List
from app.models.team_member import TeamMemberRole, TeamMemberStatus

class Permission(str, Enum):
    # Job management
    CREATE_JOB = "create_job"
    UPDATE_JOB = "update_job"
    DELETE_JOB = "delete_job"
    VIEW_JOB = "view_job"
    
    # Team management
    ADD_TEAM_MEMBER = "add_team_member"
    REMOVE_TEAM_MEMBER = "remove_team_member"
    UPDATE_TEAM_MEMBER_ROLE = "update_team_member_role"
    
    # Candidate management
    VIEW_CANDIDATES = "view_candidates"
    CHAT_WITH_CANDIDATES = "chat_with_candidates"
    
    # Job sharing
    SHARE_JOB = "share_job"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    TeamMemberRole.OWNER: [
        Permission.CREATE_JOB,
        Permission.UPDATE_JOB,
        Permission.DELETE_JOB,
        Permission.VIEW_JOB,
        Permission.ADD_TEAM_MEMBER,
        Permission.REMOVE_TEAM_MEMBER,
        Permission.UPDATE_TEAM_MEMBER_ROLE,
        Permission.VIEW_CANDIDATES,
        Permission.CHAT_WITH_CANDIDATES,
        Permission.SHARE_JOB,
    ],
    TeamMemberRole.ADMIN: [
        Permission.CREATE_JOB,
        Permission.UPDATE_JOB,
        Permission.DELETE_JOB,
        Permission.VIEW_JOB,
        Permission.ADD_TEAM_MEMBER,
        Permission.VIEW_CANDIDATES,
        Permission.CHAT_WITH_CANDIDATES,
        Permission.SHARE_JOB,
    ],
    TeamMemberRole.HR_MANAGER: [
        Permission.CREATE_JOB,
        Permission.UPDATE_JOB,
        Permission.VIEW_JOB,
        Permission.VIEW_CANDIDATES,
        Permission.CHAT_WITH_CANDIDATES,
        Permission.SHARE_JOB,
    ],
    TeamMemberRole.RECRUITER: [
        Permission.VIEW_JOB,
        Permission.VIEW_CANDIDATES,
        Permission.CHAT_WITH_CANDIDATES,
        Permission.SHARE_JOB,
    ],
    TeamMemberRole.VIEWER: [
        Permission.VIEW_JOB,
        Permission.SHARE_JOB,
    ],
}

def get_role_permissions(role: TeamMemberRole) -> List[Permission]:
    """Get permissions for a specific role"""
    return ROLE_PERMISSIONS.get(role, [])

def get_user_permissions(user_id: int, corporate_profile_id: int, db) -> List[Permission]:
    """Get user permissions for a specific corporate profile"""
    from app.repositories.team_member_repository import TeamMemberRepository
    from app.repositories.corporate_profile_repository import CorporateProfileRepository
    
    # Check if user is the owner
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(corporate_profile_id)
    
    if profile and profile.user_id == user_id:
        return ROLE_PERMISSIONS[TeamMemberRole.OWNER]
    
    # Check if user is a team member
    team_repo = TeamMemberRepository(db)
    team_member = team_repo.get_by_user_and_corporate_profile(user_id, corporate_profile_id)
    
    if not team_member or team_member.status != TeamMemberStatus.ACCEPTED:
        return []
    
    return ROLE_PERMISSIONS.get(team_member.role, [])

def has_permission(user_id: int, corporate_profile_id: int, permission: Permission, db) -> bool:
    """Check if user has specific permission for corporate profile"""
    permissions = get_user_permissions(user_id, corporate_profile_id, db)
    return permission in permissions
