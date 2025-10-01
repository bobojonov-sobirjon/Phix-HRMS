#!/usr/bin/env python3
"""
Script to completely reset database connection and alembic state
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text
import psycopg2

def reset_database_completely():
    try:
        # Get database connection details from engine
        url = str(engine.url)
        print(f"Database URL: {url}")
        
        # Parse connection details
        if url.startswith('postgresql://'):
            # Extract connection details
            parts = url.replace('postgresql://', '').split('@')
            if len(parts) == 2:
                user_pass = parts[0].split(':')
                host_db = parts[1].split('/')
                
                if len(user_pass) == 2 and len(host_db) == 2:
                    user = user_pass[0]
                    password = user_pass[1]
                    host = host_db[0].split(':')[0]
                    port = host_db[0].split(':')[1] if ':' in host_db[0] else '5432'
                    database = host_db[1]
                    
                    print(f"Connecting to: {host}:{port}/{database} as {user}")
                    
                    # Create new connection
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        database=database,
                        user=user,
                        password=password
                    )
                    
                    # Rollback any failed transaction
                    conn.rollback()
                    print("Rolled back failed transaction")
                    
                    # Reset alembic version
                    cursor = conn.cursor()
                    cursor.execute("UPDATE alembic_version SET version_num = 'merge_manual_heads'")
                    conn.commit()
                    print("Reset alembic version to merge_manual_heads")
                    
                    # Verify the change
                    cursor.execute("SELECT version_num FROM alembic_version")
                    version = cursor.fetchone()[0]
                    print(f"Current alembic version: {version}")
                    
                    cursor.close()
                    conn.close()
                    print("Database connection closed")
                    
                    return True
                    
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return False

if __name__ == "__main__":
    if reset_database_completely():
        print("Database completely reset successfully!")
    else:
        print("Failed to reset database")
        sys.exit(1)
