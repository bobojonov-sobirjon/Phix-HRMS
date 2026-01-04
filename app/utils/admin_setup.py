"""
Admin user setup utility
Creates admin user if it doesn't exist
"""
from sqlalchemy.orm import Session
from ..repositories.user_repository import UserRepository
from ..repositories.role_repository import RoleRepository
from ..db.database import SessionLocal


def create_admin_user(db: Session = None) -> bool:
    """
    Create admin user if it doesn't exist
    Email: admin@admin.com
    Password: Admin@2024!Secure#PhixHRMS
    
    Returns:
        bool: True if admin user was created or already exists, False on error
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)
        
        # Check if admin user already exists
        admin_user = user_repo.get_user_by_email("admin@admin.com")
        
        if admin_user:
            print("✅ Admin user already exists: admin@admin.com")
            return True
        
        # Get or create admin role
        admin_role = role_repo.get_role_by_name("admin")
        if not admin_role:
            print("📝 Creating admin role...")
            admin_role = role_repo.create_role("admin")
            print("✅ Admin role created")
        
        # Create admin user with secure password
        admin_password = "Admin@2024!Secure#PhixHRMS"
        
        print("📝 Creating admin user...")
        admin_user = user_repo.create_user(
            name="Admin User",
            email="admin@admin.com",
            password=admin_password,
            phone=None  # Admin doesn't need phone
        )
        
        # Assign admin role
        user_repo.assign_roles_to_user(admin_user.id, ['admin'])
        
        # Set admin as verified and active
        admin_user.is_verified = True
        admin_user.is_active = True
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@admin.com")
        print(f"   Password: {admin_password}")
        print(f"   User ID: {admin_user.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
        return False
    finally:
        if should_close:
            db.close()


def ensure_admin_user_exists():
    """
    Convenience function to ensure admin user exists
    Can be called during application startup
    """
    return create_admin_user()
