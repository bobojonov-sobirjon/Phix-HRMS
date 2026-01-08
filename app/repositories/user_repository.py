from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.user import User
from ..models.otp import OTP
from datetime import datetime, timezone
from ..models.role import Role
from ..models.user_role import UserRole
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlalchemy import and_, or_
from ..models.project import Project
from ..models.company import Company
from ..models.education_facility import EducationFacility
from ..models.certification_center import CertificationCenter
from ..models.education import Education
from ..models.experience import Experience
from ..models.certification import Certification
from .role_repository import RoleRepository

class UserRepository:
    """Repository for user database operations with optimized queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with optimized loading"""
        return self.db.query(User).options(
            selectinload(User.roles)
        ).filter(and_(User.email == email, User.is_deleted == False)).first()
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone with optimized loading"""
        return self.db.query(User).options(
            selectinload(User.roles)
        ).filter(and_(User.phone == phone, User.is_deleted == False)).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with optimized loading"""
        user = self.db.query(User).options(
            selectinload(User.roles),
            selectinload(User.skills),
            selectinload(User.location),
            selectinload(User.language),
            selectinload(User.main_category),
            selectinload(User.sub_category)
        ).filter(and_(User.id == user_id, User.is_deleted == False)).first()
        
        if user:
            user.educations = self.db.query(Education).options(
                selectinload(Education.education_facility)
            ).filter(Education.user_id == user_id, Education.is_deleted == False).all()
            
            user.experiences = self.db.query(Experience).options(
                selectinload(Experience.company_ref)
            ).filter(Experience.user_id == user_id, Experience.is_deleted == False).all()
            
            user.certifications = self.db.query(Certification).options(
                selectinload(Certification.certification_center)
            ).filter(Certification.user_id == user_id, Certification.is_deleted == False).all()
            
            user.projects = self.db.query(Project).options(
                selectinload(Project.images)
            ).filter(Project.user_id == user_id, Project.is_deleted == False).all()
        
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with all related data (alias for get_user_by_id)"""
        return self.get_user_by_id(user_id)
    
    def get_user_by_social_id(self, provider: str, social_id: str) -> Optional[User]:
        """Get user by social login ID with optimized loading"""
        query = self.db.query(User).options(
            selectinload(User.roles)
        ).filter(User.is_deleted == False)
        
        if provider == "google":
            return query.filter(User.google_id == social_id).first()
        elif provider == "facebook":
            return query.filter(User.facebook_id == social_id).first()
        elif provider == "apple":
            return query.filter(User.apple_id == social_id).first()
        return None
    
    def create_user(self, name: str, email: str, password: str = None, phone: str = None) -> User:
        """Create new user with optimized transaction"""

            
        user = User(
            name=name,
            email=email,
            phone=phone
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
            is_verified=True
        )
        
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
        self.db.query(User).filter(User.id == user_id).update({
            User.last_login: datetime.now(timezone.utc)
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
        
        try:
            for key, value in update_data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            from ..core.logging_config import logger
            logger.error(f"Error updating user profile: {e}", exc_info=True)
            raise

    def update_user_categories(self, user_id: int, main_category_id: Optional[int] = None, sub_category_id: Optional[int] = None) -> Optional[User]:
        """Update user categories with validation"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if main_category_id is not None:
            from ..models.category import Category
            main_category = self.db.query(Category).filter(Category.id == main_category_id).first()
            if not main_category:
                return None
            user.main_category_id = main_category_id
        
        if sub_category_id is not None:
            from ..models.category import Category
            sub_category = self.db.query(Category).filter(Category.id == sub_category_id).first()
            if not sub_category:
                return None
            user.sub_category_id = sub_category_id
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete user with optimized query"""
        result = self.db.query(User).filter(User.id == user_id).update({
            User.is_deleted: True
        })
        self.db.commit()
        return result > 0

    def restore_user_by_email(self, email: str) -> bool:
        """Restore user by email (set is_deleted to False)"""
        result = self.db.query(User).filter(User.email == email).update({
            User.is_deleted: False
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

    def assign_roles_to_user(self, user_id: int, role_names: List[str]) -> bool:
        """Assign multiple roles to user by role names with optimized query"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        roles = self.db.query(Role).filter(Role.name.in_(role_names)).all()
        
        if not roles:
            role_repo = RoleRepository(self.db)
            role_repo.seed_initial_roles()
            roles = self.db.query(Role).filter(Role.name.in_(role_names)).all()
        
        if roles:
            user.roles.extend(roles)
            self.db.commit()
            return True
        return False

    def get_user_full_profile(self, user_id: int) -> Optional[User]:
        """Get user full profile with optimized eager loading to prevent N+1 queries"""
        user = self.db.query(User).options(
            selectinload(User.location),
            selectinload(User.roles),
            selectinload(User.skills),
            selectinload(User.main_category),
            selectinload(User.sub_category)
        ).filter(and_(User.id == user_id, User.is_deleted == False)).first()
        
        if user:
            user.educations = self.db.query(Education).options(
                selectinload(Education.education_facility)
            ).filter(Education.user_id == user_id, Education.is_deleted == False).all()
            
            user.experiences = self.db.query(Experience).options(
                selectinload(Experience.company_ref)
            ).filter(Experience.user_id == user_id, Experience.is_deleted == False).all()
            
            user.certifications = self.db.query(Certification).options(
                selectinload(Certification.certification_center)
            ).filter(Certification.user_id == user_id, Certification.is_deleted == False).all()
            
            user.projects = self.db.query(Project).options(
                selectinload(Project.images)
            ).filter(Project.user_id == user_id, Project.is_deleted == False).all()
        
        return user
    
    def get_users_batch(self, user_ids: List[int]) -> List[User]:
        """Get multiple users in batch to avoid N+1 queries"""
        return self.db.query(User).options(
            selectinload(User.roles),
            selectinload(User.location)
        ).filter(and_(User.id.in_(user_ids), User.is_deleted == False)).all()
    
    def get_users_by_emails(self, emails: List[str]) -> List[User]:
        """Get multiple users by emails in batch"""
        return self.db.query(User).options(
            selectinload(User.roles)
        ).filter(and_(User.email.in_(emails), User.is_deleted == False)).all()
    
    def block_user(self, user_id: int, blocked_by: int, block_reason: Optional[str] = None) -> bool:
        """Block a user (set is_active to False and record blocking info)"""
        from datetime import datetime, timezone
        user = self.get_user_by_id_including_deleted(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.blocked_at = datetime.now(timezone.utc)
        user.blocked_by = blocked_by
        if block_reason:
            user.block_reason = block_reason
        
        self.db.commit()
        self.db.refresh(user)
        return True
    
    def unblock_user(self, user_id: int) -> bool:
        """Unblock a user (set is_active to True and clear blocking info)"""
        user = self.get_user_by_id_including_deleted(user_id)
        if not user:
            return False
        
        user.is_active = True
        user.blocked_at = None
        user.blocked_by = None
        user.block_reason = None
        
        self.db.commit()
        self.db.refresh(user)
        return True
    
    def get_user_by_id_including_deleted(self, user_id: int) -> Optional[User]:
        """Get user by ID including deleted users (for admin operations)"""
        return self.db.query(User).options(
            selectinload(User.roles),
            selectinload(User.skills),
            selectinload(User.location),
            selectinload(User.language),
            selectinload(User.main_category),
            selectinload(User.sub_category)
        ).filter(User.id == user_id).first()
    
    def get_all_users_with_filters(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> tuple[List[User], int]:
        """Get all users with filters and pagination (for admin)"""
        from sqlalchemy import or_
        
        query = self.db.query(User).options(
            selectinload(User.roles),
            selectinload(User.location),
            selectinload(User.language),
            selectinload(User.main_category),
            selectinload(User.sub_category)
        )
        
        if is_deleted is not None:
            query = query.filter(User.is_deleted == is_deleted)
        else:
            query = query.filter(User.is_deleted == False)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        if search:
            query = query.filter(
                or_(
                    User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        
        if date_from:
            query = query.filter(User.created_at >= date_from)
        
        if date_to:
            query = query.filter(User.created_at <= date_to)
        
        if role:
            query = query.join(UserRole).join(Role).filter(Role.name.ilike(f"%{role}%"))
        
        total = query.count()
        
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return users, total

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
    
    def create_otp_with_type(self, email: str, otp_code: str, otp_type: str = "password_reset") -> OTP:
        """Create new OTP with specific type (registration or password_reset)"""
        otp = OTP.create_otp(email, otp_code, otp_type)
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        return otp
    
    def create_otp_with_data(self, email: str, otp_code: str, otp_type: str = "password_reset", data: dict = None) -> OTP:
        """Create new OTP with specific type and additional data"""
        otp = OTP.create_otp(email, otp_code, otp_type, data)
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
                OTP.expires_at > datetime.now(timezone.utc)
            )
        ).first()
    
    def get_valid_otp_by_type(self, email: str, otp_code: str, otp_type: str) -> Optional[OTP]:
        """Get valid OTP for email, code and type with optimized query"""
        return self.db.query(OTP).filter(
            and_(
                OTP.email == email,
                OTP.otp_code == otp_code,
                OTP.otp_type == otp_type,
                OTP.is_used == False,
                OTP.expires_at > datetime.now(timezone.utc)
            )
        ).first()
    
    def mark_otp_used(self, otp_id: int):
        """Mark OTP as used with optimized query"""
        self.db.query(OTP).filter(OTP.id == otp_id).update({
            OTP.is_used: True
        })
        self.db.commit()
    
    def delete_expired_otps(self):
        """Delete expired OTPs with optimized query"""
        from datetime import datetime
        self.db.query(OTP).filter(OTP.expires_at < datetime.now(timezone.utc)).delete()
        self.db.commit()
    
    def cleanup_old_otps(self, days_old: int = 7):
        """Clean up old OTPs to prevent database bloat"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        self.db.query(OTP).filter(OTP.created_at < cutoff_date).delete()
        self.db.commit() 