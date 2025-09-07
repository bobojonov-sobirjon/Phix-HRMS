from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.models.team_member import TeamMember, TeamMemberStatus
from app.models.user import User
from app.models.corporate_profile import CorporateProfile
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate
from sqlalchemy import func


class TeamMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_team_member(self, team_member: TeamMemberCreate, corporate_profile_id: int, invited_by_user_id: int) -> TeamMember:
        """Create a new team member invitation"""
        # Check if user exists
        user = self.db.query(User).filter(User.email == team_member.email).first()
        if not user:
            raise ValueError("User with this email does not exist")
        
        # Check if user is already a team member
        existing_member = self.db.query(TeamMember).filter(
            and_(
                TeamMember.corporate_profile_id == corporate_profile_id,
                TeamMember.user_id == user.id
            )
        ).first()
        
        if existing_member:
            raise ValueError("User is already a team member of this company")
        
        # Create new team member
        db_team_member = TeamMember(
            corporate_profile_id=corporate_profile_id,
            user_id=user.id,
            invited_by_user_id=invited_by_user_id,
            role=team_member.role,
            status=TeamMemberStatus.PENDING
        )
        
        self.db.add(db_team_member)
        self.db.commit()
        self.db.refresh(db_team_member)
        return db_team_member

    def get_team_members(self, corporate_profile_id: int, skip: int = 0, limit: int = 100) -> List[TeamMember]:
        """Get all team members for a corporate profile"""
        return self.db.query(TeamMember).filter(
            TeamMember.corporate_profile_id == corporate_profile_id
        ).offset(skip).limit(limit).all()

    def get_team_member_by_id(self, team_member_id: int) -> Optional[TeamMember]:
        """Get team member by ID"""
        return self.db.query(TeamMember).filter(TeamMember.id == team_member_id).first()

    def get_team_member_by_user_and_company(self, user_id: int, corporate_profile_id: int) -> Optional[TeamMember]:
        """Get team member by user ID and corporate profile ID"""
        return self.db.query(TeamMember).filter(
            and_(
                TeamMember.user_id == user_id,
                TeamMember.corporate_profile_id == corporate_profile_id
            )
        ).first()

    def update_team_member_role(self, team_member_id: int, role_update: TeamMemberUpdate) -> Optional[TeamMember]:
        """Update team member role"""
        team_member = self.get_team_member_by_id(team_member_id)
        if not team_member:
            return None
        
        if role_update.role:
            team_member.role = role_update.role
        
        self.db.commit()
        self.db.refresh(team_member)
        return team_member

    def update_team_member_status(self, team_member_id: int, status: bool) -> Optional[TeamMember]:
        """Update team member status (True for accept, False for reject)"""
        team_member = self.get_team_member_by_id(team_member_id)
        if not team_member:
            return None
        
        if status:
            team_member.status = TeamMemberStatus.ACCEPTED
            team_member.accepted_at = self.db.query(func.now()).scalar()
        else:
            team_member.status = TeamMemberStatus.REJECTED
            team_member.rejected_at = self.db.query(func.now()).scalar()
        
        self.db.commit()
        self.db.refresh(team_member)
        return team_member

    def remove_team_member(self, team_member_id: int) -> bool:
        """Remove team member from company"""
        team_member = self.get_team_member_by_id(team_member_id)
        if not team_member:
            return False
        
        self.db.delete(team_member)
        self.db.commit()
        return True

    def search_users(self, query: str, skip: int = 0, limit: int = 20) -> List[User]:
        """Search users by name or email"""
        # Simple user search
        users = self.db.query(User).filter(
            and_(
                or_(
                    User.name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%")
                ),
                User.is_active == True,
                User.is_deleted == False
            )
        ).offset(skip).limit(limit).all()
        
        return users

    def get_team_member_count(self, corporate_profile_id: int) -> int:
        """Get total count of team members for a corporate profile"""
        return self.db.query(TeamMember).filter(
            TeamMember.corporate_profile_id == corporate_profile_id
        ).count()

    def get_pending_invitations(self, user_id: int) -> List[TeamMember]:
        """Get pending invitations for a user"""
        return self.db.query(TeamMember).filter(
            and_(
                TeamMember.user_id == user_id,
                TeamMember.status == TeamMemberStatus.PENDING
            )
        ).all()

    def create_admin_member(self, corporate_profile_id: int, user_id: int) -> TeamMember:
        """Create admin team member for corporate profile creator"""
        from app.models.team_member import TeamMemberRole
        
        # Create admin team member
        db_team_member = TeamMember(
            corporate_profile_id=corporate_profile_id,
            user_id=user_id,
            invited_by_user_id=user_id,  # Self-invited as admin
            role=TeamMemberRole.ADMIN,
            status=TeamMemberStatus.ACCEPTED  # Auto-accepted for creator
        )
        
        self.db.add(db_team_member)
        self.db.commit()
        self.db.refresh(db_team_member)
        return db_team_member

    def get_user_team_memberships(self, user_id: int) -> List[TeamMember]:
        """Get all team memberships for a user (accepted invitations)"""
        return self.db.query(TeamMember).filter(
            and_(
                TeamMember.user_id == user_id,
                TeamMember.status == TeamMemberStatus.ACCEPTED
            )
        ).all()

    def get_user_team_memberships_all_statuses(self, user_id: int) -> List[TeamMember]:
        """Get all team memberships for a user (all statuses)"""
        return self.db.query(TeamMember).filter(
            TeamMember.user_id == user_id
        ).all()