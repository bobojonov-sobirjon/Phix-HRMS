#!/usr/bin/env python3
"""
Fix email configuration script
This script helps diagnose and fix Gmail SMTP issues
"""

import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

def test_gmail_smtp():
    """Test Gmail SMTP with different configurations"""
    print("📧 Testing Gmail SMTP Configuration")
    print("=" * 50)
    
    # Get current settings
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "sobirbobojonov2000@gmail.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "deellqvnevnehcqba")
    
    print(f"📧 Current Settings:")
    print(f"   Server: {smtp_server}:{smtp_port}")
    print(f"   Username: {smtp_username}")
    print(f"   Password: {'*' * len(smtp_password)}")
    
    # Test different configurations
    test_configs = [
        {
            "name": "Current Configuration",
            "server": smtp_server,
            "port": smtp_port,
            "username": smtp_username,
            "password": smtp_password
        },
        {
            "name": "Gmail with App Password (Recommended)",
            "server": "smtp.gmail.com",
            "port": 587,
            "username": "sobirbobojonov2000@gmail.com",
            "password": "your-app-password-here"  # You'll need to replace this
        }
    ]
    
    for config in test_configs:
        print(f"\n🔍 Testing: {config['name']}")
        print("-" * 30)
        
        try:
            # Test connection
            print("   Connecting to SMTP server...")
            server = smtplib.SMTP(config["server"], config["port"])
            print("   ✅ SMTP connection established!")
            
            # Test TLS
            print("   Starting TLS...")
            server.starttls()
            print("   ✅ TLS started successfully!")
            
            # Test authentication
            print("   Attempting login...")
            server.login(config["username"], config["password"])
            print("   ✅ Authentication successful!")
            
            # Test email sending
            print("   Sending test email...")
            msg = MIMEMultipart()
            msg['From'] = config["username"]
            msg['To'] = "sobirbobojonov05763104@gmail.com"  # Your email
            msg['Subject'] = "Test Email from Phix HRMS"
            
            body = """
            <html>
            <body>
                <h2>Test Email</h2>
                <p>This is a test email from Phix HRMS to verify email configuration.</p>
                <p>If you receive this email, your SMTP configuration is working correctly!</p>
                <p>Time: {}</p>
            </body>
            </html>
            """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            msg.attach(MIMEText(body, 'html'))
            
            text = msg.as_string()
            server.sendmail(config["username"], "sobirbobojonov05763104@gmail.com", text)
            print("   ✅ Test email sent successfully!")
            
            server.quit()
            print(f"   🎉 {config['name']} is working!")
            return config
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Authentication failed: {e}")
            if "Application-specific password" in str(e):
                print("   💡 This is expected - you need to use an App Password")
            elif "Username and Password not accepted" in str(e):
                print("   💡 Check your username and password")
        except smtplib.SMTPException as e:
            print(f"   ❌ SMTP Error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    
    return None

def setup_gmail_app_password():
    """Instructions for setting up Gmail App Password"""
    print("\n📋 Gmail App Password Setup Instructions:")
    print("=" * 50)
    print("1. Go to your Google Account settings:")
    print("   https://myaccount.google.com/")
    print("\n2. Navigate to Security → 2-Step Verification")
    print("   (Enable 2-Step Verification if not already enabled)")
    print("\n3. Scroll down to 'App passwords'")
    print("\n4. Click 'Select app' and choose 'Mail'")
    print("\n5. Click 'Select device' and choose 'Other (Custom name)'")
    print("\n6. Enter 'Phix HRMS' as the name")
    print("\n7. Click 'Generate'")
    print("\n8. Copy the 16-character password (e.g., 'abcd efgh ijkl mnop')")
    print("\n9. Update your .env file with the new password:")
    print("   SMTP_PASSWORD=your-16-character-app-password")
    print("\n10. Restart the server and test again")

def create_updated_env():
    """Create updated .env file with proper email configuration"""
    print("\n🔧 Creating updated .env file...")
    
    env_content = """# Database Configuration
DATABASE_URL=postgresql://postgres:0576@localhost:5432/phix_hrms

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-2024
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration for OTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=sobirbobojonov2000@gmail.com
SMTP_PASSWORD=your-app-password-here

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
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file updated!")
        print("📝 Please update SMTP_PASSWORD with your Gmail App Password")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Fix Email Configuration")
    print("=" * 40)
    
    # Test current configuration
    working_config = test_gmail_smtp()
    
    if working_config:
        print(f"\n✅ Email configuration is working!")
        print(f"   Using: {working_config['name']}")
    else:
        print("\n❌ Email configuration failed!")
        print("\n💡 The issue is likely with Gmail authentication.")
        print("   Gmail requires either:")
        print("   1. 2-Factor Authentication + App Password")
        print("   2. Less secure app access (not recommended)")
        
        setup_gmail_app_password()
        create_updated_env()
        
        print("\n🔄 After setting up the App Password:")
        print("1. Update the .env file with your App Password")
        print("2. Restart the server")
        print("3. Test the forgot password endpoint again")

if __name__ == "__main__":
    from datetime import datetime
    main() 