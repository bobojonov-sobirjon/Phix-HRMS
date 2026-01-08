from enum import Enum
from typing import List
from app.models.team_member import TeamMemberRole, TeamMemberStatus

class Permission(str, Enum):
    CREATE_JOB = "create_job"
    UPDATE_JOB = "update_job"
    DELETE_JOB = "delete_job"
    VIEW_JOB = "view_job"
    
    ADD_TEAM_MEMBER = "add_team_member"
    REMOVE_TEAM_MEMBER = "remove_team_member"
    UPDATE_TEAM_MEMBER_ROLE = "update_team_member_role"
    
    VIEW_CANDIDATES = "view_candidates"
    CHAT_WITH_CANDIDATES = "chat_with_candidates"
    
    SHARE_JOB = "share_job"

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
    
    corporate_repo = CorporateProfileRepository(db)
    profile = corporate_repo.get_by_id(corporate_profile_id)
    
    if profile and profile.user_id == user_id:
        return ROLE_PERMISSIONS[TeamMemberRole.OWNER]
    
    team_repo = TeamMemberRepository(db)
    team_member = team_repo.get_by_user_and_corporate_profile(user_id, corporate_profile_id)
    
    if not team_member or team_member.status != TeamMemberStatus.ACCEPTED:
        return []
    
    return ROLE_PERMISSIONS.get(team_member.role, [])

def has_permission(user_id: int, corporate_profile_id: int, permission: Permission, db) -> bool:
    """Check if user has specific permission for corporate profile"""
    permissions = get_user_permissions(user_id, corporate_profile_id, db)
    return permission in permissions

def is_admin_user(user_email: str) -> bool:
    """Check if user is admin (admin@admin.com)"""
    return user_email.lower() == "admin@admin.com"

def check_admin_or_owner(user_email: str, user_id: int, owner_id: int) -> bool:
    """Check if user is admin or owner of the resource"""
    return is_admin_user(user_email) or user_id == owner_id