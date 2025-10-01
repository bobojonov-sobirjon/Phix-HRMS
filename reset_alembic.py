#!/usr/bin/env python3
"""
Script to reset alembic version table and clear failed transaction state
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

def reset_alembic_state():
    try:
        with engine.connect() as conn:
            # Rollback any failed transaction
            conn.execute(text('ROLLBACK'))
            print("Rolled back failed transaction")
            
            # Reset alembic version to merge_manual_heads
            conn.execute(text("UPDATE alembic_version SET version_num = 'merge_manual_heads'"))
            conn.commit()
            print("Reset alembic version to merge_manual_heads")
            
            # Verify the change
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()[0]
            print(f"Current alembic version: {version}")
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if reset_alembic_state():
        print("Database state reset successfully!")
    else:
        print("Failed to reset database state")
        sys.exit(1)
