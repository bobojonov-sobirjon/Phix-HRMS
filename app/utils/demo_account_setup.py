"""
Demo Account Setup Utility

This module provides functionality to create a demo account with:
- Fixed credentials (email & password)
- Permanent OTP code for testing

Usage:
    python -m app.utils.demo_account_setup
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from ..db.database import SessionLocal
from ..models.user import User
from ..models.otp import OTP
from ..utils.auth import get_password_hash


# Demo account configuration
DEMO_CONFIG = {
    "email": "cheker@test.com",
    "password": "12345678@#hello_phix",
    "name": "Demo User",
    "permanent_otp": "12345",  # 5-digit permanent OTP
    "otp_types": ["password_reset", "email_verification", "corporate_verification"]
}


def create_demo_user(db: Session) -> User:
    """
    Create demo user with fixed credentials.
    
    Args:
        db: Database session
        
    Returns:
        User: Created or existing demo user
    """
    # Check if demo user already exists
    existing_user = db.query(User).filter(
        User.email == DEMO_CONFIG["email"]
    ).first()
    
    if existing_user:
        print(f"[OK] Demo user already exists: {DEMO_CONFIG['email']}")
        return existing_user
    
    # Create new demo user
    password_hash = get_password_hash(DEMO_CONFIG["password"])
    
    demo_user = User(
        email=DEMO_CONFIG["email"],
        password_hash=password_hash,
        name=DEMO_CONFIG["name"],
        is_active=True,
        is_verified=True,  # Pre-verified for demo
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    
    print(f"[OK] Demo user created successfully: {DEMO_CONFIG['email']}")
    return demo_user


def create_permanent_otp(db: Session, otp_type: str = "password_reset") -> OTP:
    """
    Create permanent OTP for demo account.
    
    This OTP never expires and can be used multiple times for testing.
    
    Args:
        db: Database session
        otp_type: Type of OTP (password_reset, email_verification, etc.)
        
    Returns:
        OTP: Created permanent OTP
    """
    # Delete existing OTPs for this email and type
    db.query(OTP).filter(
        OTP.email == DEMO_CONFIG["email"],
        OTP.otp_type == otp_type
    ).delete()
    
    # Create permanent OTP (expires in 10 years)
    permanent_otp = OTP(
        email=DEMO_CONFIG["email"],
        otp_code=DEMO_CONFIG["permanent_otp"],
        otp_type=otp_type,
        is_used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3650),  # 10 years
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(permanent_otp)
    db.commit()
    db.refresh(permanent_otp)
    
    print(f"[OK] Permanent OTP created for {otp_type}: {DEMO_CONFIG['permanent_otp']}")
    return permanent_otp


def setup_demo_account() -> dict:
    """
    Setup complete demo account with user and permanent OTPs.
    
    This function:
    1. Creates demo user with fixed credentials
    2. Creates permanent OTP codes for all types
    3. Returns setup information
    
    Returns:
        dict: Setup information including user details and OTP codes
    """
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("Setting up Demo Account...")
        print("=" * 70)
        
        # Step 1: Create demo user
        demo_user = create_demo_user(db)
        
        # Step 2: Create permanent OTPs for all types
        otps_created = []
        for otp_type in DEMO_CONFIG["otp_types"]:
            otp = create_permanent_otp(db, otp_type)
            otps_created.append({
                "type": otp_type,
                "code": otp.otp_code,
                "expires_at": otp.expires_at
            })
        
        # Setup complete
        setup_info = {
            "user": {
                "id": demo_user.id,
                "email": demo_user.email,
                "name": demo_user.name,
                "password": DEMO_CONFIG["password"],  # For testing only
                "is_verified": demo_user.is_verified
            },
            "otps": otps_created
        }
        
        print("=" * 70)
        print("Demo Account Setup Complete!")
        print("=" * 70)
        print("")
        print("Demo Account Credentials:")
        print(f"   Email:    {setup_info['user']['email']}")
        print(f"   Password: {setup_info['user']['password']}")
        print(f"   User ID:  {setup_info['user']['id']}")
        print("")
        print("Permanent OTP Codes:")
        for otp_info in otps_created:
            print(f"   {otp_info['type']}: {otp_info['code']}")
        print("")
        print("Usage:")
        print("   1. Login with email and password to get access token")
        print("   2. Use OTP code '12345' for any verification (never expires)")
        print("   3. Test forgot password, corporate profile, etc.")
        print("=" * 70)
        
        return setup_info
        
    except Exception as e:
        print(f"[ERROR] Demo account setup failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_demo_account() -> bool:
    """
    Verify that demo account exists and is properly configured.
    
    Returns:
        bool: True if demo account exists and is valid
    """
    db = SessionLocal()
    
    try:
        # Check user
        user = db.query(User).filter(User.email == DEMO_CONFIG["email"]).first()
        if not user:
            print("[WARNING] Demo user not found")
            return False
        
        # Check OTPs
        otps = db.query(OTP).filter(
            OTP.email == DEMO_CONFIG["email"],
            OTP.otp_code == DEMO_CONFIG["permanent_otp"]
        ).all()
        
        if len(otps) < len(DEMO_CONFIG["otp_types"]):
            print("[WARNING] Not all OTP types configured")
            return False
        
        print("[OK] Demo account verified successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Demo account verification failed: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    """Run demo account setup when executed directly"""
    try:
        setup_demo_account()
        
        # Verify setup
        if verify_demo_account():
            print("\nDemo account is ready to use!")
        else:
            print("\n[ERROR] Demo account verification failed!")
            
    except Exception as e:
        print(f"\n[ERROR] Setup failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
