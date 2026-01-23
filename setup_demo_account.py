#!/usr/bin/env python3
"""
Setup Demo Account - Command Line Script

This script sets up a demo account for testing purposes.

Usage:
    python setup_demo_account.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.demo_account_setup import setup_demo_account, verify_demo_account


def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("  PHIX HRMS - Demo Account Setup")
    print("=" * 70 + "\n")
    
    try:
        # Setup demo account
        setup_info = setup_demo_account()
        
        # Verify setup
        print("\nVerifying demo account setup...")
        if verify_demo_account():
            print("[OK] Demo account verified successfully!")
            print("\n" + "=" * 70)
            print("  Setup Complete - Ready for Testing!")
            print("=" * 70 + "\n")
            return 0
        else:
            print("[ERROR] Demo account verification failed!")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
