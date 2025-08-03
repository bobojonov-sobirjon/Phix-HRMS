#!/usr/bin/env python3
"""
Database setup script for Phix HRMS
This script helps you create the database and run migrations with optimizations
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="0576"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'phix_hrms'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE phix_hrms")
        else:
            pass
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        return False
    
    return True

def run_migrations():
    """Run Alembic migrations"""
    try:
        result = os.system("alembic upgrade head")
        if result == 0:
            return True
        else:
            return False
    except Exception as e:
        return False

def seed_initial_data():
    """Seed initial data like roles"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.repositories.role_repository import RoleRepository
        
        # Create database engine
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:0576@localhost:5432/phix_hrms")
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create session and seed roles
        db = SessionLocal()
        role_repo = RoleRepository(db)
        role_repo.seed_initial_roles()
        db.close()
        
        return True
    except Exception as e:
        return False

def create_performance_indexes():
    """Create database indexes for better performance"""
    try:
        
        # Connect to the phix_hrms database
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="0576",
            database="phix_hrms"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # List of indexes to create
        indexes = [
            # Users table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_facebook_id ON users(facebook_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_apple_id ON users(apple_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # OTPs table indexes
            "CREATE INDEX IF NOT EXISTS idx_otps_email ON otps(email)",
            "CREATE INDEX IF NOT EXISTS idx_otps_email_expires ON otps(email, expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_otps_is_used ON otps(is_used)",
            "CREATE INDEX IF NOT EXISTS idx_otps_created_at ON otps(created_at)",
            
            # Locations table indexes
            "CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name)",
            "CREATE INDEX IF NOT EXISTS idx_locations_code ON locations(code)",
            "CREATE INDEX IF NOT EXISTS idx_locations_is_deleted ON locations(is_deleted)",
            
            # Skills table indexes
            "CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)",
            "CREATE INDEX IF NOT EXISTS idx_skills_is_deleted ON skills(is_deleted)",
            
            # User skills table indexes
            "CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_skills_skill_id ON user_skills(skill_id)",
            
            # Companies table indexes
            "CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)",
            "CREATE INDEX IF NOT EXISTS idx_companies_country ON companies(country)",
            "CREATE INDEX IF NOT EXISTS idx_companies_is_deleted ON companies(is_deleted)",
            
            # Education facilities table indexes
            "CREATE INDEX IF NOT EXISTS idx_education_facilities_name ON education_facilities(name)",
            "CREATE INDEX IF NOT EXISTS idx_education_facilities_country ON education_facilities(country)",
            "CREATE INDEX IF NOT EXISTS idx_education_facilities_is_deleted ON education_facilities(is_deleted)",
            
            # Certification centers table indexes
            "CREATE INDEX IF NOT EXISTS idx_certification_centers_name ON certification_centers(name)",
            "CREATE INDEX IF NOT EXISTS idx_certification_centers_country ON certification_centers(country)",
            "CREATE INDEX IF NOT EXISTS idx_certification_centers_is_deleted ON certification_centers(is_deleted)",
            
            # Projects table indexes
            "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_projects_is_deleted ON projects(is_deleted)",
            
            # Project images table indexes
            "CREATE INDEX IF NOT EXISTS idx_project_images_project_id ON project_images(project_id)",
            
            # Composite indexes for better query performance
            "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_otps_email_used_expires ON otps(email, is_used, expires_at)",
        ]
        
        # Execute each index creation
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                pass
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        return False

def optimize_database_settings():
    """Optimize PostgreSQL settings for better performance"""
    try:
        
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="0576",
            database="phix_hrms"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Database optimization settings
        optimizations = [
            "ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements'",
            "ALTER SYSTEM SET max_connections = 200",
            "ALTER SYSTEM SET shared_buffers = '256MB'",
            "ALTER SYSTEM SET effective_cache_size = '1GB'",
            "ALTER SYSTEM SET maintenance_work_mem = '64MB'",
            "ALTER SYSTEM SET checkpoint_completion_target = 0.9",
            "ALTER SYSTEM SET wal_buffers = '16MB'",
            "ALTER SYSTEM SET default_statistics_target = 100",
            "ALTER SYSTEM SET random_page_cost = 1.1",
            "ALTER SYSTEM SET effective_io_concurrency = 200",
            "ALTER SYSTEM SET work_mem = '4MB'",
            "ALTER SYSTEM SET min_wal_size = '1GB'",
            "ALTER SYSTEM SET max_wal_size = '4GB'",
        ]
        
        for optimization in optimizations:
            try:
                cursor.execute(optimization)
            except Exception as e:
                pass
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        return False

def main():
    """Main setup function with optimizations"""
    
    # Step 1: Create database
    if create_database():
        pass
    else:
        return
    
    # Step 2: Run migrations
    if run_migrations():
        pass
    else:
        return
    
    # Step 3: Seed initial data (roles)
    if seed_initial_data():
        pass
    else:
        pass
    
    # Step 4: Create performance indexes
    if create_performance_indexes():
        pass
    else:
        pass
    
    # Step 5: Optimize database settings
    if optimize_database_settings():
        pass
    else:
        pass

if __name__ == "__main__":
    main() 