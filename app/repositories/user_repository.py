from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User
from ..models.otp import OTP
from datetime import datetime
from ..models.role import Role
from sqlalchemy.orm import joinedload
from ..models.project import Project
from ..models.company import Company
from ..models.education_facility import EducationFacility
from ..models.certification_center import CertificationCenter
from ..models.education import Education
from ..models.experience import Experience
from ..models.certification import Certification

class UserRepository:
    """Repository for user database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_social_id(self, provider: str, social_id: str) -> Optional[User]:
        """Get user by social login ID"""
        if provider == "google":
            return self.db.query(User).filter(User.google_id == social_id).first()
        elif provider == "facebook":
            return self.db.query(User).filter(User.facebook_id == social_id).first()
        elif provider == "apple":
            return self.db.query(User).filter(User.apple_id == social_id).first()
        return None
    
    def create_user(self, name: str, email: str, password: str = None) -> User:
        """Create new user"""
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
        """Create new user via social login"""
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
        """Update user's last login time"""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
    
    def update_user_password(self, user_id: int, new_password: str):
        """Update user password"""
        user = self.get_user_by_id(user_id)
        if user:
            user.set_password(new_password)
            self.db.commit()

    def update_user_profile(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user profile fields, including language_id"""
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
        """Soft delete user by setting is_deleted to True"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_deleted = True
        self.db.commit()
        return True

    def assign_role_to_user(self, user_id: int, role_id: int):
        user = self.get_user_by_id(user_id)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if user and role:
            user.roles.append(role)
            self.db.commit()
            return True
        return False

    def get_user_full_profile(self, user_id: int) -> Optional[User]:
        return self.db.query(User).options(
            joinedload(User.location),
            joinedload(User.roles),
            joinedload(User.educations).joinedload(Education.education_facility_ref),
            joinedload(User.experiences).joinedload(Experience.company_ref),
            joinedload(User.certifications).joinedload(Certification.certification_center_ref),
            joinedload(User.projects).joinedload(Project.images),
            joinedload(User.skills)
        ).filter(User.id == user_id).first()

class OTPRepository:
    """Repository for OTP database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_otp(self, email: str, otp_code: str) -> OTP:
        """Create new OTP"""
        otp = OTP.create_otp(email, otp_code)
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        return otp
    
    def get_valid_otp(self, email: str, otp_code: str) -> Optional[OTP]:
        """Get valid OTP for email and code"""
        return self.db.query(OTP).filter(
            OTP.email == email,
            OTP.otp_code == otp_code,
            OTP.is_used == False
        ).first()
    
    def mark_otp_used(self, otp_id: int):
        """Mark OTP as used"""
        otp = self.db.query(OTP).filter(OTP.id == otp_id).first()
        if otp:
            otp.is_used = True
            self.db.commit()
    
    def delete_expired_otps(self):
        """Delete expired OTPs"""
        from datetime import datetime
        self.db.query(OTP).filter(OTP.expires_at < datetime.utcnow()).delete()
        self.db.commit() 