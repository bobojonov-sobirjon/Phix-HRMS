#!/usr/bin/env python3
"""
Email configuration test script
This script helps test and debug email settings
"""

import smtplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection with different configurations"""
    print("📧 Testing SMTP Configuration")
    print("=" * 50)
    
    # Get settings from environment
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "sobirbobojonov2000@gmail.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "deellqvnevnehcqba")
    
    print(f"📧 Server: {smtp_server}:{smtp_port}")
    print(f"📧 Username: {smtp_username}")
    print(f"📧 Password: {'*' * len(smtp_password)}")
    
    try:
        print("\n🔍 Testing SMTP connection...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("✅ SMTP connection established!")
        
        print("\n🔍 Testing TLS...")
        server.starttls()
        print("✅ TLS started successfully!")
        
        print("\n🔍 Testing authentication...")
        server.login(smtp_username, smtp_password)
        print("✅ Authentication successful!")
        
        print("\n🔍 Testing email sending...")
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = smtp_username  # Send to yourself for testing
        msg['Subject'] = "Test Email from Phix HRMS"
        
        body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email from Phix HRMS to verify email configuration.</p>
            <p>If you receive this email, your SMTP configuration is working correctly!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        text = msg.as_string()
        server.sendmail(smtp_username, smtp_username, text)
        print("✅ Test email sent successfully!")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Solutions:")
        print("1. Enable 2-Factor Authentication on your Gmail account")
        print("2. Generate an App Password:")
        print("   - Go to Google Account settings")
        print("   - Security → 2-Step Verification → App passwords")
        print("   - Generate password for 'Mail'")
        print("   - Use the generated password instead of your regular password")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_gmail_app_password():
    """Instructions for setting up Gmail App Password"""
    print("\n📋 Gmail App Password Setup Instructions:")
    print("=" * 50)
    print("1. Go to your Google Account settings:")
    print("   https://myaccount.google.com/")
    print("\n2. Navigate to Security → 2-Step Verification")
    print("\n3. Scroll down to 'App passwords'")
    print("\n4. Select 'Mail' and 'Other (Custom name)'")
    print("\n5. Enter 'Phix HRMS' as the name")
    print("\n6. Click 'Generate'")
    print("\n7. Copy the 16-character password")
    print("\n8. Update your .env file:")
    print("   SMTP_PASSWORD=your-16-character-app-password")
    print("\n9. Restart the server and test again")

def main():
    """Main function"""
    print("🚀 Email Configuration Test")
    print("=" * 40)
    
    # Test SMTP connection
    success = test_smtp_connection()
    
    if not success:
        print("\n❌ Email configuration failed!")
        test_gmail_app_password()
    else:
        print("\n✅ Email configuration is working!")
        print("\n🎉 You can now use the forgot password feature!")

if __name__ == "__main__":
    main() 