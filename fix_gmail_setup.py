#!/usr/bin/env python3
"""
Gmail SMTP Configuration Fix
This script helps you fix the Gmail SMTP authentication error
"""

import os
import webbrowser
import getpass

def create_env_file():
    """Create or update .env file with proper Gmail configuration"""
    print("🔧 Setting up Gmail SMTP Configuration")
    print("=" * 50)
    
    # Get user input
    print("\n📧 Please provide your Gmail credentials:")
    email = input("Enter your Gmail address: ").strip()
    
    if not email or '@gmail.com' not in email:
        print("❌ Please enter a valid Gmail address")
        return False
    
    print("\n🔑 For the password, you need to use a Gmail App Password, not your regular password.")
    print("If you haven't set up App Password yet, follow these steps:")
    
    # Ask if user wants to open Gmail settings
    choice = input("\n🌐 Would you like to open Google Account settings to set up App Password? (y/n): ")
    if choice.lower() == 'y':
        webbrowser.open("https://myaccount.google.com/security")
        print("\n📋 Steps to create App Password:")
        print("1. Go to Security section")
        print("2. Enable 2-Step Verification if not already enabled")
        print("3. Go to 'App passwords'")
        print("4. Select 'Mail' as the app")
        print("5. Select 'Other (Custom name)' as device")
        print("6. Enter 'Phix HRMS' as the name")
        print("7. Click 'Generate'")
        print("8. Copy the 16-character password")
    
    app_password = getpass.getpass("Enter your Gmail App Password (16 characters): ").strip()
    
    if len(app_password) != 16:
        print("❌ App Password should be 16 characters long")
        return False
    
    # Create .env content
    env_content = f"""# Database Configuration
DATABASE_URL=postgresql://postgres:0576@localhost:5432/phix_hrms

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration for OTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME={email}
SMTP_PASSWORD={app_password}

# OTP Configuration
OTP_EXPIRE_MINUTES=5
OTP_LENGTH=6

# Social Login Configuration
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Facebook OAuth
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/facebook/callback

# Apple OAuth
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
APPLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/apple/callback
"""
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("\n✅ .env file created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_email_configuration():
    """Test the email configuration"""
    print("\n🧪 Testing Email Configuration")
    print("=" * 35)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_username or not smtp_password:
            print("❌ SMTP credentials not found in .env file")
            return False
        
        print(f"📧 Testing with: {smtp_username}")
        
        # Import and test email function
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = smtp_username  # Send to self for testing
        msg['Subject'] = "Test Email - Phix HRMS"
        
        body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email from Phix HRMS.</p>
            <p>If you receive this, your email configuration is working correctly!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Test SMTP connection
        print("📧 Connecting to SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        print("📧 Attempting login...")
        server.login(smtp_username, smtp_password)
        print("✅ Login successful!")
        
        print("📧 Sending test email...")
        text = msg.as_string()
        server.sendmail(smtp_username, smtp_username, text)
        print("✅ Test email sent successfully!")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("💡 Make sure you're using App Password, not your regular Gmail password")
        return False
    except Exception as e:
        print(f"❌ Error testing email: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Gmail SMTP Configuration Fix")
    print("=" * 40)
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("📁 .env file found")
        choice = input("Do you want to recreate it? (y/n): ")
        if choice.lower() != 'y':
            print("Using existing .env file")
        else:
            if create_env_file():
                print("✅ .env file updated")
            else:
                print("❌ Failed to create .env file")
                return
    else:
        print("📁 No .env file found, creating one...")
        if not create_env_file():
            print("❌ Failed to create .env file")
            return
    
    # Test the configuration
    if test_email_configuration():
        print("\n🎉 Email configuration is working correctly!")
        print("🔄 Please restart your server to apply the changes:")
        print("   python -m uvicorn app.main:app --host 192.168.1.39 --port 8000")
    else:
        print("\n❌ Email configuration failed")
        print("📋 Please check your Gmail App Password setup")

if __name__ == "__main__":
    main() 