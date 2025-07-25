#!/usr/bin/env python3
"""
Test database connection script
This script helps diagnose database connection issues
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection with different methods"""
    print("🔍 Testing database connection...")
    print("=" * 50)
    
    # Method 1: Direct psycopg2 connection
    print("1. Testing direct psycopg2 connection...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="0576",
            database="phix_hrms"
        )
        print("✅ Direct connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
    
    # Method 2: Connection string
    print("\n2. Testing connection string...")
    try:
        conn_string = "postgresql://postgres:0576@localhost:5432/phix_hrms"
        conn = psycopg2.connect(conn_string)
        print("✅ Connection string successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Connection string failed: {e}")
    
    # Method 3: Environment variable
    print("\n3. Testing environment variable...")
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:0576@localhost:5432/phix_hrms")
        print(f"Database URL: {db_url}")
        conn = psycopg2.connect(db_url)
        print("✅ Environment variable connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Environment variable connection failed: {e}")

def check_postgres_service():
    """Check if PostgreSQL service is running"""
    print("\n🔍 Checking PostgreSQL service...")
    try:
        import subprocess
        result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL service is running!")
        else:
            print("❌ PostgreSQL service is not running!")
            print(f"Error: {result.stderr}")
    except FileNotFoundError:
        print("⚠️  pg_isready command not found. Please check if PostgreSQL is installed.")

if __name__ == "__main__":
    check_postgres_service()
    test_connection() 