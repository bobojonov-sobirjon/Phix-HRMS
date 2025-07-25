#!/usr/bin/env python3
"""
Database setup script for Phix HRMS
This script helps you create the database and run migrations
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
            print("Creating database 'phix_hrms'...")
            cursor.execute("CREATE DATABASE phix_hrms")
            print("✅ Database 'phix_hrms' created successfully!")
        else:
            print("✅ Database 'phix_hrms' already exists!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def run_migrations():
    """Run Alembic migrations"""
    try:
        print("Running database migrations...")
        result = os.system("alembic upgrade head")
        if result == 0:
            print("✅ Migrations completed successfully!")
            return True
        else:
            print("❌ Migration failed with exit code:", result)
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Phix HRMS Database...")
    print("=" * 50)
    
    # Step 1: Create database
    if create_database():
        print("\n📊 Database setup completed!")
    else:
        print("\n❌ Database setup failed!")
        return
    
    # Step 2: Run migrations
    if run_migrations():
        print("\n🔄 Migration setup completed!")
    else:
        print("\n❌ Migration setup failed!")
        return
    
    print("\n🎉 Database setup completed successfully!")
    print("\nYou can now run the application with:")
    print("python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 