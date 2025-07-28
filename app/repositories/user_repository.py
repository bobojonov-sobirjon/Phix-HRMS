from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.user import User
from ..models.otp import OTP
from datetime import datetime
from ..models.role import Role
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlalchemy import and_, or_
from ..models.project import Project
from ..models.company import Company
from ..models.education_facility import EducationFacility
from ..models.certification_center import CertificationCenter
from ..models.education import Education
from ..models.experience import Experience
from ..models.certification import Certification

class UserRepository:
    """Repository for user database operations with optimized queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with optimized loading"""
        return self.db.query(User).options(
            selectinload(User.roles)  # Eager load roles to avoid N+1
        ).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with optimized loading"""
        return self.db.query(User).options(
            selectinload(User.roles)  # Eager load roles to avoid N+1
        ).filter(User.id == user_id).first()
    
    def get_user_by_social_id(self, provider: str, social_id: str) -> Optional[User]:
        """Get user by social login ID with optimized loading"""
        query = self.db.query(User).options(
            selectinload(User.roles)  # Eager load roles to avoid N+1
        )
        
        if provider == "google":
            return query.filter(User.google_id == social_id).first()
        elif provider == "facebook":
            return query.filter(User.facebook_id == social_id).first()
        elif provider == "apple":
            return query.filter(User.apple_id == social_id).first()
        return None
    
    def create_user(self, name: str, email: str, password: str = None) -> User:
        """Create new user with optimized transaction"""
        user = User(
            name=name,
            email=email
        )
        if password:
            user.set_password(password)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def create_social_user(self, name: str, email: str, provider: str, social_id: str, avatar_url: str = None) -> User:
        """Create new user via social login with optimized transaction"""
        user = User(
            name=name,
            email=email,
            avatar_url=avatar_url,
            is_verified=True  # Social users are pre-verified
        )
        
        # Set social ID based on provider
        if provider == "google":
            user.google_id = social_id
        elif provider == "facebook":
            user.facebook_id = social_id
        elif provider == "apple":
            user.apple_id = social_id
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user_id: int):
        """Update user's last login time with optimized query"""
        # Use direct update instead of loading user first
        self.db.query(User).filter(User.id == user_id).update({
            User.last_login: datetime.utcnow()
        })
        self.db.commit()
    
    def update_user_password(self, user_id: int, new_password: str):
        """Update user password with optimized query"""
        user = self.get_user_by_id(user_id)
        if user:
            user.set_password(new_password)
            self.db.commit()

    def update_user_profile(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user profile fields with optimized query"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete user with optimized query"""
        # Use direct update instead of loading user first
        result = self.db.query(User).filter(User.id == user_id).update({
            User.is_deleted: True
        })
        self.db.commit()
        return result > 0

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Assign role to user with optimized query"""
        user = self.get_user_by_id(user_id)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if user and role:
            user.roles.append(role)
            self.db.commit()
            return True
        return False

    def get_user_full_profile(self, user_id: int) -> Optional[User]:
        """Get user full profile with optimized eager loading to prevent N+1 queries"""
        return self.db.query(User).options(
            # Use selectinload for better performance than joinedload
            selectinload(User.location),
            selectinload(User.roles),
            selectinload(User.educations).selectinload(Education.education_facility_ref),
            selectinload(User.experiences).selectinload(Experience.company_ref),
            selectinload(User.certifications).selectinload(Certification.certification_center_ref),
            selectinload(User.projects).selectinload(Project.images),
            selectinload(User.skills)
        ).filter(User.id == user_id).first()
    
    def get_users_batch(self, user_ids: List[int]) -> List[User]:
        """Get multiple users in batch to avoid N+1 queries"""
        return self.db.query(User).options(
            selectinload(User.roles),
            selectinload(User.location)
        ).filter(User.id.in_(user_ids)).all()
    
    def get_users_by_emails(self, emails: List[str]) -> List[User]:
        """Get multiple users by emails in batch"""
        return self.db.query(User).options(
            selectinload(User.roles)
        ).filter(User.email.in_(emails)).all()

class OTPRepository:
    """Repository for OTP database operations with optimized queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_otp(self, email: str, otp_code: str) -> OTP:
        """Create new OTP with optimized transaction"""
        otp = OTP.create_otp(email, otp_code)
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        return otp
    
    def get_valid_otp(self, email: str, otp_code: str) -> Optional[OTP]:
        """Get valid OTP for email and code with optimized query"""
        return self.db.query(OTP).filter(
            and_(
                OTP.email == email,
                OTP.otp_code == otp_code,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()  # Add expiration check
            )
        ).first()
    
    def mark_otp_used(self, otp_id: int):
        """Mark OTP as used with optimized query"""
        # Use direct update instead of loading OTP first
        self.db.query(OTP).filter(OTP.id == otp_id).update({
            OTP.is_used: True
        })
        self.db.commit()
    
    def delete_expired_otps(self):
        """Delete expired OTPs with optimized query"""
        from datetime import datetime
        self.db.query(OTP).filter(OTP.expires_at < datetime.utcnow()).delete()
        self.db.commit()
    
    def cleanup_old_otps(self, days_old: int = 7):
        """Clean up old OTPs to prevent database bloat"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        self.db.query(OTP).filter(OTP.created_at < cutoff_date).delete()
        self.db.commit() 