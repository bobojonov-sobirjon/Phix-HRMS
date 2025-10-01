#!/usr/bin/env python3
"""
Script to create all database tables from SQLAlchemy models
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database and Base
from app.database import Base, engine

# Import all models to register them with Base
from app.models.user import User
from app.models.otp import OTP
from app.models.location import Location
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.company import Company
from app.models.education_facility import EducationFacility
from app.models.certification_center import CertificationCenter
from app.models.project import Project
from app.models.project_image import ProjectImage
from app.models.education import Education
from app.models.experience import Experience
from app.models.certification import Certification
from app.models.corporate_profile import CorporateProfile
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.team_member import TeamMember
from app.models.gig_job import GigJob
from app.models.gig_job_skill import GigJobSkill
from app.models.full_time_job import FullTimeJob
from app.models.full_time_job_skill import FullTimeJobSkill
from app.models.proposal import Proposal
from app.models.saved_job import SavedJob
from app.models.contact_us import ContactUs
from app.models.faq import FAQ
from app.models.category import Category
from app.models.chat import ChatRoom, ChatParticipant, ChatMessage, UserPresence

def create_all_tables():
    """Create all tables from models"""
    try:
        print("Creating all tables from SQLAlchemy models...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Total tables created: {len(tables)}")
        print(f"Tables: {tables}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    if create_all_tables():
        print("\n✅ Database tables created successfully!")
        print("You can now run: alembic stamp head")
    else:
        print("\n❌ Failed to create database tables")
        sys.exit(1)

