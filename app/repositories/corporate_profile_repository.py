from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.corporate_profile import CorporateProfile
from ..models.user import User
from ..models.team_member import TeamMember
from ..schemas.corporate_profile import CorporateProfileCreate, CorporateProfileUpdate


class CorporateProfileRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, corporate_profile: CorporateProfileCreate, user_id: int) -> CorporateProfile:
        """Create a new corporate profile"""
        db_corporate_profile = CorporateProfile(
            **corporate_profile.dict(),
            user_id=user_id
        )
        self.db.add(db_corporate_profile)
        self.db.commit()
        self.db.refresh(db_corporate_profile)
        return db_corporate_profile
    
    def get_by_id(self, profile_id: int) -> Optional[CorporateProfile]:
        """Get corporate profile by ID"""
        return self.db.query(CorporateProfile).options(
            joinedload(CorporateProfile.location),
            joinedload(CorporateProfile.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.invited_by)
        ).filter(
            CorporateProfile.id == profile_id
        ).first()
    
    def get_by_user_id(self, user_id: int) -> Optional[CorporateProfile]:
        """Get corporate profile by user ID (excluding deleted)"""
        return self.db.query(CorporateProfile).options(
            joinedload(CorporateProfile.location),
            joinedload(CorporateProfile.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.invited_by)
        ).filter(
            and_(
                CorporateProfile.user_id == user_id,
                CorporateProfile.is_deleted == False
            )
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[CorporateProfile]:
        """Get all corporate profiles with pagination"""
        return self.db.query(CorporateProfile).options(
            joinedload(CorporateProfile.location),
            joinedload(CorporateProfile.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.invited_by)
        ).offset(skip).limit(limit).all()
    
    def get_active_profiles(self, skip: int = 0, limit: int = 100) -> List[CorporateProfile]:
        """Get only active corporate profiles"""
        return self.db.query(CorporateProfile).options(
            joinedload(CorporateProfile.location),
            joinedload(CorporateProfile.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.user),
            joinedload(CorporateProfile.team_members).joinedload(TeamMember.invited_by)
        ).filter(
            CorporateProfile.is_active == True
        ).offset(skip).limit(limit).all()
    
    def update(self, profile_id: int, corporate_profile: CorporateProfileUpdate) -> Optional[CorporateProfile]:
        """Update corporate profile"""
        db_profile = self.get_by_id(profile_id)
        if not db_profile:
            return None
        
        update_data = corporate_profile.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)
        
        self.db.commit()
        self.db.refresh(db_profile)
        return db_profile
    
    def delete(self, profile_id: int) -> bool:
        """Delete corporate profile"""
        db_profile = self.get_by_id(profile_id)
        if not db_profile:
            return False
        
        self.db.delete(db_profile)
        self.db.commit()
        return True
    
    def verify_profile(self, profile_id: int) -> Optional[CorporateProfile]:
        """Verify and activate corporate profile"""
        db_profile = self.get_by_id(profile_id)
        if not db_profile:
            return None
        
        db_profile.is_verified = True
        db_profile.is_active = True
        
        self.db.commit()
        self.db.refresh(db_profile)
        return db_profile
    
    def check_user_has_profile(self, user_id: int) -> bool:
        """Check if user already has a corporate profile"""
        profile = self.get_by_user_id(user_id)
        return profile is not None
    
    def get_verified_profiles(self, skip: int = 0, limit: int = 100) -> List[CorporateProfile]:
        """Get only verified corporate profiles"""
        return self.db.query(CorporateProfile).filter(
            CorporateProfile.is_verified == True
        ).offset(skip).limit(limit).all()
    
    def count_total(self) -> int:
        """Get total count of corporate profiles"""
        return self.db.query(CorporateProfile).count()
    
    def count_active(self) -> int:
        """Get count of active corporate profiles"""
        return self.db.query(CorporateProfile).filter(
            CorporateProfile.is_active == True
        ).count()
    
    def count_verified(self) -> int:
        """Get count of verified corporate profiles"""
        return self.db.query(CorporateProfile).filter(
            CorporateProfile.is_verified == True
        ).count()