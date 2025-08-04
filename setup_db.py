#!/usr/bin/env python3
"""
Database setup script for Phix HRMS
This script helps set up the database, create tables, and initialize data
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import Base, engine
from app.models import (
    User, Role, UserRole, Skill, UserSkill, Location, 
    Education, Experience, Project, ProjectImage, 
    Certification, CertificationCenter,
    Language, OTP
)
from app.models.contact_us import ContactUs
from app.models.faq import FAQ

# Load environment variables
load_dotenv()

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def drop_tables():
    """Drop all database tables"""
    print("Dropping all database tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("✓ Database tables dropped successfully")
        return True
    except Exception as e:
        print(f"✗ Error dropping tables: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        # Create a test connection
        test_engine = create_engine(os.getenv("DATABASE_URL", "postgresql://postgres:0576@localhost:5432/phix_hrms"))
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def create_default_roles():
    """Create default roles"""
    print("Creating default roles...")
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if roles already exist
        existing_roles = db.query(Role).all()
        if existing_roles:
            print("Roles already exist, skipping...")
            db.close()
            return True
        
        # Create default roles
        roles = [
            Role(name="user", description="Regular user"),
            Role(name="admin", description="Administrator"),
            Role(name="moderator", description="Moderator"),
            Role(name="manager", description="Manager")
        ]
        
        for role in roles:
            db.add(role)
        
        db.commit()
        print("✓ Default roles created successfully")
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error creating roles: {e}")
        return False

def create_default_skills():
    """Create default skills"""
    print("Creating default skills...")
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if skills already exist
        existing_skills = db.query(Skill).all()
        if existing_skills:
            print("Skills already exist, skipping...")
            db.close()
            return True
        
        # Create default skills
        skills = [
            Skill(name="Python", description="Python programming language"),
            Skill(name="JavaScript", description="JavaScript programming language"),
            Skill(name="React", description="React.js framework"),
            Skill(name="Django", description="Django web framework"),
            Skill(name="FastAPI", description="FastAPI web framework"),
            Skill(name="PostgreSQL", description="PostgreSQL database"),
            Skill(name="Docker", description="Docker containerization"),
            Skill(name="Git", description="Git version control"),
            Skill(name="AWS", description="Amazon Web Services"),
            Skill(name="Linux", description="Linux administration")
        ]
        
        for skill in skills:
            db.add(skill)
        
        db.commit()
        print("✓ Default skills created successfully")
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error creating skills: {e}")
        return False

def create_default_locations():
    """Create default locations"""
    print("Creating default locations...")
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if locations already exist
        existing_locations = db.query(Location).all()
        if existing_locations:
            print("Locations already exist, skipping...")
            db.close()
            return True
        
        # Create default locations
        locations = [
            Location(name="Tashkent", country="Uzbekistan", flag_image="/static/flags/uzbekistan_images.png"),
            Location(name="New York", country="USA", flag_image="/static/flags/usa.png"),
            Location(name="London", country="UK", flag_image="/static/flags/uk.png"),
            Location(name="Berlin", country="Germany", flag_image="/static/flags/germany.png"),
            Location(name="Tokyo", country="Japan", flag_image="/static/flags/japan.png")
        ]
        
        for location in locations:
            db.add(location)
        
        db.commit()
        print("✓ Default locations created successfully")
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error creating locations: {e}")
        return False

def create_admin_user():
    """Create a default admin user"""
    print("Creating admin user...")
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@phixhrms.com").first()
        if admin_user:
            print("Admin user already exists, skipping...")
            db.close()
            return True
        
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@phixhrms.com",
            is_active=True,
            is_verified=True,
            is_social_user=False
        )
        admin_user.set_password("admin123")  # Change this password!
        
        db.add(admin_user)
        db.commit()
        
        # Assign admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.add(user_role)
            db.commit()
        
        print("✓ Admin user created successfully")
        print("Email: admin@phixhrms.com")
        print("Password: admin123 (CHANGE THIS!)")
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        return False

def setup_database():
    """Complete database setup"""
    print("=== Database Setup for Phix HRMS ===")
    print()
    
    # Test database connection
    if not test_database_connection():
        print("Database connection failed. Please check your DATABASE_URL in .env file")
        return False
    
    # Create tables
    if not create_tables():
        print("Failed to create tables")
        return False
    
    # Create default data
    create_default_roles()
    create_default_skills()
    create_default_locations()
    create_admin_user()
    
    print()
    print("=== Database Setup Complete ===")
    print("Your database is now ready to use!")
    return True

def reset_database():
    """Reset database (drop and recreate all tables)"""
    print("=== Database Reset ===")
    print("WARNING: This will delete all data!")
    
    confirm = input("Are you sure you want to reset the database? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Database reset cancelled")
        return False
    
    # Drop tables
    if not drop_tables():
        print("Failed to drop tables")
        return False
    
    # Create tables
    if not create_tables():
        print("Failed to create tables")
        return False
    
    # Create default data
    create_default_roles()
    create_default_skills()
    create_default_locations()
    create_admin_user()
    
    print()
    print("=== Database Reset Complete ===")
    print("Database has been reset and initialized!")
    return True

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_database()
        elif command == "reset":
            reset_database()
        elif command == "test":
            test_database_connection()
        elif command == "create-tables":
            create_tables()
        elif command == "drop-tables":
            drop_tables()
        elif command == "create-roles":
            create_default_roles()
        elif command == "create-skills":
            create_default_skills()
        elif command == "create-locations":
            create_default_locations()
        elif command == "create-admin":
            create_admin_user()
        else:
            print("Unknown command. Available commands:")
            print("  setup          - Complete database setup")
            print("  reset          - Reset database (drop and recreate)")
            print("  test           - Test database connection")
            print("  create-tables  - Create all tables")
            print("  drop-tables    - Drop all tables")
            print("  create-roles   - Create default roles")
            print("  create-skills  - Create default skills")
            print("  create-locations - Create default locations")
            print("  create-admin   - Create admin user")
    else:
        # Default: complete setup
        setup_database()

if __name__ == "__main__":
    main() 