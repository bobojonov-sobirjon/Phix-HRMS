#!/usr/bin/env python3
"""
Complete Database Reset and Setup Script

This script will:
1. Drop existing database
2. Create fresh database
3. Create ENUM types
4. Create all tables
5. Stamp Alembic
6. Restart server

Usage:
    python reset_database.py
"""
import sys
import os
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_command(command, description):
    """Run shell command and print result"""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print('='*70)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ {description} - FAILED")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ {description} - ERROR: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("\n" + "="*70)
    print("  PHIX HRMS - Complete Database Reset")
    print("="*70)
    print("\n⚠️  WARNING: This will DELETE all data in phix_hrms database!")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        return 1
    
    # Step 1: Drop and recreate database
    drop_create_sql = """
DROP DATABASE IF EXISTS phix_hrms;
CREATE DATABASE phix_hrms;
"""
    
    if not run_command(
        f"sudo -u postgres psql -c \"{drop_create_sql.strip().replace(chr(10), ' ')}\"",
        "Step 1: Drop and Create Database"
    ):
        print("\n✗ Failed to reset database")
        return 1
    
    # Step 2: Create ENUM types
    enum_sql = """
DO $$ 
BEGIN
    CREATE TYPE devicetype AS ENUM ('ios', 'android');
    CREATE TYPE notificationtype AS ENUM ('proposal_received', 'proposal_accepted', 'proposal_rejected', 'job_posted', 'message_received', 'system');
    CREATE TYPE messagetype AS ENUM ('text', 'image', 'video', 'audio', 'file', 'voice');
    CREATE TYPE experiencelevel AS ENUM ('entry', 'junior', 'mid', 'senior', 'lead', 'director');
    CREATE TYPE jobtype AS ENUM ('full_time', 'part_time', 'contract', 'internship');
    CREATE TYPE workmode AS ENUM ('on_site', 'remote', 'hybrid');
    CREATE TYPE jobstatus AS ENUM ('draft', 'active', 'closed', 'expired');
    CREATE TYPE proposalstatus AS ENUM ('pending', 'accepted', 'rejected', 'withdrawn');
    CREATE TYPE companysize AS ENUM ('1-10', '10-50', '50-200', '200-1000', '1000+');
END $$;
"""
    
    enum_file = "/tmp/create_enums.sql"
    with open(enum_file, 'w') as f:
        f.write(enum_sql)
    
    if not run_command(
        f"sudo -u postgres psql -d phix_hrms -f {enum_file}",
        "Step 2: Create ENUM Types"
    ):
        print("\n⚠️  ENUM creation had errors, but continuing...")
    
    # Step 3: Create tables with SQLAlchemy
    python_script = """
import sys
sys.path.insert(0, '/var/www/Phix-HRMS')
from app.db.database import Base, engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('All tables created successfully')
"""
    
    python_file = "/tmp/create_tables.py"
    with open(python_file, 'w') as f:
        f.write(python_script)
    
    if not run_command(
        f"python3 {python_file}",
        "Step 3: Create All Tables"
    ):
        print("\n✗ Failed to create tables")
        return 1
    
    # Step 4: Stamp Alembic
    if not run_command(
        "alembic stamp head",
        "Step 4: Stamp Alembic"
    ):
        print("\n⚠️  Alembic stamp had errors, but continuing...")
    
    # Step 5: Restart server
    if not run_command(
        "sudo systemctl restart phix-hrms",
        "Step 5: Restart Server"
    ):
        print("\n⚠️  Server restart failed, you may need to restart manually")
    
    # Cleanup temp files
    try:
        os.remove(enum_file)
        os.remove(python_file)
    except:
        pass
    
    # Success
    print("\n" + "="*70)
    print("  ✓ Database Reset Complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Check server status: sudo systemctl status phix-hrms")
    print("  2. Test API: curl http://localhost:8000/")
    print("  3. Open Swagger: http://your-server/docs")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
