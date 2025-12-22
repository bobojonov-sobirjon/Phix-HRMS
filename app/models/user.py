from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
import bcrypt
from .language import Language

class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic user information
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for social login users
    
    # Social login fields
    google_id = Column(String(255), unique=True, nullable=True)
    facebook_id = Column(String(255), unique=True, nullable=True)
    apple_id = Column(String(255), unique=True, nullable=True)
    
    # Profile information
    phone = Column(String(20), unique=True, nullable=True)
    avatar_url = Column(Text, nullable=True)
    about_me = Column(Text, nullable=True)
    current_position = Column(String(255), nullable=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=True)
    
    # Category information
    main_category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    sub_category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Blocking fields
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    block_reason = Column(Text, nullable=True)
    blocked_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    location = relationship('Location', back_populates='users')
    language = relationship('Language')
    main_category = relationship('Category', foreign_keys=[main_category_id], back_populates='users_main')
    sub_category = relationship('Category', foreign_keys=[sub_category_id], back_populates='users_sub')
    certifications = relationship('Certification', back_populates='user', cascade='all, delete-orphan')
    educations = relationship('Education', back_populates='user', cascade='all, delete-orphan')
    experiences = relationship('Experience', back_populates='user', cascade='all, delete-orphan')
    projects = relationship('Project', back_populates='user', cascade='all, delete-orphan')
    skills = relationship('Skill', secondary='user_skills', back_populates='users', viewonly=True)
    roles = relationship('Role', secondary='user_roles', back_populates='users')
    gig_jobs = relationship('GigJob', back_populates='author', cascade='all, delete-orphan')
    corporate_profile = relationship('CorporateProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    team_memberships = relationship('TeamMember', foreign_keys='TeamMember.user_id', back_populates='user')
    proposals = relationship('Proposal', back_populates='user', cascade='all, delete-orphan')
    saved_jobs = relationship('SavedJob', back_populates='user', cascade='all, delete-orphan')
    device_tokens = relationship('UserDeviceToken', back_populates='user', cascade='all, delete-orphan')
    corporate_profile_follows = relationship('CorporateProfileFollow', back_populates='user', cascade='all, delete-orphan')
    notifications = relationship('Notification', foreign_keys='Notification.recipient_user_id', back_populates='recipient', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def is_social_user(self) -> bool:
        """Check if user registered via social login"""
        return bool(self.google_id or self.facebook_id or self.apple_id) 