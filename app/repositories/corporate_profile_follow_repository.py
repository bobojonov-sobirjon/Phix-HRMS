from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from app.models.corporate_profile_follow import CorporateProfileFollow
from app.models.corporate_profile import CorporateProfile
from app.models.user import User
from app.schemas.corporate_profile_follow import CorporateProfileFollowCreate
from app.pagination import PaginationParams


class CorporateProfileFollowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, corporate_profile_id: int, user_id: int) -> CorporateProfileFollow:
        """Create a new corporate profile follow"""
        # Check if already following
        existing = self.get_by_user_and_profile(user_id=user_id, corporate_profile_id=corporate_profile_id)
        if existing:
            raise ValueError("Already following this corporate profile")

        # Check if corporate profile exists
        corporate_profile = self.db.query(CorporateProfile).filter(
            CorporateProfile.id == corporate_profile_id,
            CorporateProfile.is_deleted == False
        ).first()
        
        if not corporate_profile:
            raise ValueError("Corporate profile not found")

        db_follow = CorporateProfileFollow(
            user_id=user_id,
            corporate_profile_id=corporate_profile_id
        )
        self.db.add(db_follow)
        self.db.commit()
        self.db.refresh(db_follow)
        return db_follow

    def get_by_id(self, follow_id: int) -> Optional[CorporateProfileFollow]:
        """Get follow by ID with relationships"""
        return self.db.query(CorporateProfileFollow).options(
            joinedload(CorporateProfileFollow.user).joinedload(User.location),
            joinedload(CorporateProfileFollow.user).joinedload(User.main_category),
            joinedload(CorporateProfileFollow.user).joinedload(User.sub_category),
            joinedload(CorporateProfileFollow.user).joinedload(User.skills),
            joinedload(CorporateProfileFollow.corporate_profile).joinedload(CorporateProfile.location),
            joinedload(CorporateProfileFollow.corporate_profile).joinedload(CorporateProfile.user),
            joinedload(CorporateProfileFollow.corporate_profile).joinedload(CorporateProfile.team_members)
        ).filter(CorporateProfileFollow.id == follow_id).first()

    def get_by_user_and_profile(
        self, 
        user_id: int, 
        corporate_profile_id: int
    ) -> Optional[CorporateProfileFollow]:
        """Get follow by user and corporate profile IDs"""
        return self.db.query(CorporateProfileFollow).filter(
            and_(
                CorporateProfileFollow.user_id == user_id,
                CorporateProfileFollow.corporate_profile_id == corporate_profile_id
            )
        ).first()

    def get_user_following(
        self, 
        user_id: int, 
        pagination: PaginationParams
    ) -> tuple[List[CorporateProfileFollow], int]:
        """Get paginated corporate profiles that user is following with full details"""
        # First get total count
        total = self.db.query(CorporateProfileFollow).join(CorporateProfile).filter(
            and_(
                CorporateProfileFollow.user_id == user_id,
                CorporateProfile.is_deleted == False
            )
        ).count()
        
        # Then get paginated results with relationships
        query = self.db.query(CorporateProfileFollow).options(
            joinedload(CorporateProfileFollow.corporate_profile).joinedload(CorporateProfile.location),
            joinedload(CorporateProfileFollow.corporate_profile).joinedload(CorporateProfile.user),
            joinedload(CorporateProfileFollow.corporate_profile).joinedload(CorporateProfile.team_members)
        ).join(CorporateProfile).filter(
            and_(
                CorporateProfileFollow.user_id == user_id,
                CorporateProfile.is_deleted == False
            )
        ).order_by(CorporateProfileFollow.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
        
        follows = query.all()
        
        return follows, total

    def get_corporate_profile_followers(
        self, 
        corporate_profile_id: int, 
        pagination: PaginationParams
    ) -> tuple[List[CorporateProfileFollow], int]:
        """Get paginated users who follow a corporate profile with full user details"""
        # First get total count
        total = self.db.query(CorporateProfileFollow).join(User).filter(
            and_(
                CorporateProfileFollow.corporate_profile_id == corporate_profile_id,
                User.is_deleted == False
            )
        ).count()
        
        # Then get paginated results with relationships
        query = self.db.query(CorporateProfileFollow).options(
            joinedload(CorporateProfileFollow.user).joinedload(User.location),
            joinedload(CorporateProfileFollow.user).joinedload(User.main_category),
            joinedload(CorporateProfileFollow.user).joinedload(User.sub_category),
            joinedload(CorporateProfileFollow.user).joinedload(User.skills),
            joinedload(CorporateProfileFollow.user).joinedload(User.roles),
            joinedload(CorporateProfileFollow.user).joinedload(User.educations),
            joinedload(CorporateProfileFollow.user).joinedload(User.experiences),
            joinedload(CorporateProfileFollow.user).joinedload(User.certifications),
            joinedload(CorporateProfileFollow.user).joinedload(User.projects),
            joinedload(CorporateProfileFollow.user).joinedload(User.language)
        ).join(User).filter(
            and_(
                CorporateProfileFollow.corporate_profile_id == corporate_profile_id,
                User.is_deleted == False
            )
        ).order_by(CorporateProfileFollow.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
        
        follows = query.all()
        
        return follows, total

    def delete(self, corporate_profile_id: int, user_id: int) -> bool:
        """Delete follow (unfollow) by corporate_profile_id and user_id"""
        follow = self.db.query(CorporateProfileFollow).filter(
            and_(
                CorporateProfileFollow.user_id == user_id,
                CorporateProfileFollow.corporate_profile_id == corporate_profile_id
            )
        ).first()
        
        if not follow:
            return False
        
        self.db.delete(follow)
        self.db.commit()
        return True

    def delete_by_id(self, follow_id: int, user_id: int) -> bool:
        """Delete follow (unfollow) by follow_id"""
        follow = self.db.query(CorporateProfileFollow).filter(
            and_(
                CorporateProfileFollow.id == follow_id,
                CorporateProfileFollow.user_id == user_id
            )
        ).first()
        
        if not follow:
            return False
        
        self.db.delete(follow)
        self.db.commit()
        return True

    def is_following(self, user_id: int, corporate_profile_id: int) -> bool:
        """Check if user is following a corporate profile"""
        follow = self.get_by_user_and_profile(user_id, corporate_profile_id)
        result = follow is not None
        return result

    def count_followers(self, corporate_profile_id: int) -> int:
        """Count total number of followers for a corporate profile (excluding deleted users)"""
        return self.db.query(CorporateProfileFollow).join(User).filter(
            and_(
                CorporateProfileFollow.corporate_profile_id == corporate_profile_id,
                User.is_deleted == False
            )
        ).count()

