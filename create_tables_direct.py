#!/usr/bin/env python3
"""
Create all database tables directly using SQLAlchemy
(Bypass Alembic migrations for fresh database)

Usage:
    python create_tables_direct.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import Base, engine
from app.models import (
    User, Role, UserRole, Skill, UserSkill, Education, Experience, Certification,
    Project, ProjectImage, Language, Location, OTP, Company, EducationFacility,
    CertificationCenter, GigJob, Proposal, ProposalAttachment, SavedJob,
    CorporateProfile, FullTimeJob, TeamMember, Category,
    ChatRoom, ChatMessage, ChatParticipant, UserPresence,
    UserDeviceToken, Notification, AgoraChannel
)


def create_all_tables():
    """Create all database tables using SQLAlchemy"""
    try:
        print("=" * 70)
        print("  Creating All Database Tables")
        print("=" * 70)
        print()
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        print()
        print("=" * 70)
        print("  ✓ All tables created successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run: alembic stamp head")
        print("  2. Restart server: sudo systemctl restart phix-hrms")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("  ✗ Failed to create tables!")
        print("=" * 70)
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if create_all_tables():
        sys.exit(0)
    else:
        sys.exit(1)
