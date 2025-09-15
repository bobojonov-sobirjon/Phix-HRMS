from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TeamMemberRole(str, Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    HR_MANAGER = "HR Manager"
    RECRUITER = "Recruiter"
    VIEWER = "Viewer"


class TeamMemberStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TeamMemberBase(BaseModel):
    role: TeamMemberRole


class TeamMemberCreate(TeamMemberBase):
    email: EmailStr


class TeamMemberUpdate(BaseModel):
    role: Optional[TeamMemberRole] = None


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    user_avatar: Optional[str] = None
    role: TeamMemberRole
    status: TeamMemberStatus
    invited_by_user_id: int
    invited_by_name: str
    created_at: datetime
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamMemberListResponse(BaseModel):
    team_members: List[TeamMemberResponse]
    total: int


class UserSearchResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    avatar_url: Optional[str] = None
    current_position: Optional[str] = None


class InvitationResponse(BaseModel):
    message: str
    team_member_id: int


class StatusUpdateRequest(BaseModel):
    status: bool  # True for accept, False for reject