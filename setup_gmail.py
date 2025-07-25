#!/usr/bin/env python3
"""
Gmail App Password Setup Guide
This script provides step-by-step instructions to set up Gmail for email sending
"""

import webbrowser
import os

def open_gmail_settings():
    """Open Gmail settings in browser"""
    print("🌐 Opening Google Account settings...")
    webbrowser.open("https://myaccount.google.com/")

def setup_instructions():
    """Display step-by-step setup instructions"""
    print("📋 Gmail App Password Setup Guide")
    print("=" * 50)
    print("\n🔧 Step-by-Step Instructions:")
    print("\n1. 📱 Enable 2-Factor Authentication:")
    print("   - Go to https://myaccount.google.com/")
    print("   - Click 'Security'")
    print("   - Click '2-Step Verification'")
    print("   - Follow the setup process")
    
    print("\n2. 🔑 Generate App Password:")
    print("   - Go back to Security")
    print("   - Click '2-Step Verification'")
    print("   - Scroll down to 'App passwords'")
    print("   - Click 'Select app' → 'Mail'")
    print("   - Click 'Select device' → 'Other (Custom name)'")
    print("   - Enter 'Phix HRMS' as the name")
    print("   - Click 'Generate'")
    
    print("\n3. 📝 Copy the App Password:")
    print("   - You'll see a 16-character password")
    print("   - Example: 'abcd efgh ijkl mnop'")
    print("   - Copy this password")
    
    print("\n4. 🔧 Update Configuration:")
    print("   - Open the .env file")
    print("   - Find the line: SMTP_PASSWORD=your-app-password-here")
    print("   - Replace 'your-app-password-here' with your App Password")
    print("   - Save the file")
    
    print("\n5. 🔄 Restart Server:")
    print("   - Stop the current server (Ctrl+C)")
    print("   - Start it again: python -m uvicorn app.main:app --reload")
    
    print("\n6. 🧪 Test Email:")
    print("   - Run: python test_email.py")
    print("   - Or test the forgot password endpoint")

def check_current_setup():
    """Check current email configuration"""
    print("🔍 Checking Current Email Configuration")
    print("=" * 40)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        smtp_username = os.getenv("SMTP_USERNAME", "Not set")
        smtp_password = os.getenv("SMTP_PASSWORD", "Not set")
        
        print(f"📧 Current Settings:")
        print(f"   Username: {smtp_username}")
        print(f"   Password: {'*' * len(smtp_password) if smtp_password != 'Not set' else 'Not set'}")
        
        if smtp_password == "your-app-password-here" or smtp_password == "deellqvnevnehcqba":
            print("\n⚠️  You need to update the SMTP_PASSWORD with your Gmail App Password")
            return False
        else:
            print("\n✅ SMTP_PASSWORD is configured")
            return True
            
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Gmail Email Setup")
    print("=" * 30)
    
    # Check current setup
    is_configured = check_current_setup()
    
    if not is_configured:
        print("\n📋 You need to set up Gmail App Password")
        setup_instructions()
        
        # Ask if user wants to open Gmail settings
        try:
            choice = input("\n🌐 Would you like to open Google Account settings? (y/n): ")
            if choice.lower() == 'y':
                open_gmail_settings()
        except KeyboardInterrupt:
            print("\n👋 Setup cancelled")
            return
        
        print("\n📝 After setting up the App Password:")
        print("1. Update the .env file")
        print("2. Restart the server")
        print("3. Test with: python test_email.py")
    else:
        print("\n✅ Email configuration looks good!")
        print("🧪 Test it with: python test_email.py")

if __name__ == "__main__":
    main() 