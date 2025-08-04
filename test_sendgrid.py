#!/usr/bin/env python3
"""
Test SendGrid configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sendgrid_config():
    """Test SendGrid configuration"""
    print("=== SendGrid Configuration Test ===")
    print()
    
    # Check API key
    api_key = os.getenv("SENDGRID_API_KEY")
    if api_key:
        print(f"✓ SendGrid API Key: {api_key[:10]}...{api_key[-10:]}")
    else:
        print("✗ SendGrid API Key not found")
        return False
    
    # Check from email
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    if from_email:
        print(f"✓ From Email: {from_email}")
    else:
        print("✗ From Email not configured")
        return False
    
    # Test SendGrid import
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        print("✓ SendGrid package installed")
    except ImportError:
        print("✗ SendGrid package not installed. Run: pip install sendgrid")
        return False
    
    # Test API connection
    try:
        sg = SendGridAPIClient(api_key=api_key)
        print("✓ SendGrid API connection successful")
        return True
    except Exception as e:
        print(f"✗ SendGrid API connection failed: {e}")
        return False

def test_sendgrid_email():
    """Test sending a test email"""
    print()
    print("=== SendGrid Email Test ===")
    
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM_EMAIL")
        
        # Create test email
        message = Mail(
            from_email=from_email,
            to_emails="test@example.com",  # Replace with your email
            subject="SendGrid Test Email",
            html_content="<h2>SendGrid Test</h2><p>This is a test email from your server.</p>"
        )
        
        # Send email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            print("✓ Test email sent successfully!")
            return True
        else:
            print(f"✗ Test email failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Test email error: {e}")
        return False

def main():
    print("Testing SendGrid configuration...")
    print()
    
    if test_sendgrid_config():
        print()
        print("Configuration is correct!")
        print()
        
        # Ask if user wants to test sending
        test_send = input("Do you want to test sending an email? (y/n): ").strip().lower()
        if test_send == 'y':
            test_email = input("Enter your email address for testing: ").strip()
            if test_email:
                # Update the test email function to use the provided email
                try:
                    from sendgrid import SendGridAPIClient
                    from sendgrid.helpers.mail import Mail
                    
                    api_key = os.getenv("SENDGRID_API_KEY")
                    from_email = os.getenv("SENDGRID_FROM_EMAIL")
                    
                    message = Mail(
                        from_email=from_email,
                        to_emails=test_email,
                        subject="SendGrid Test Email",
                        html_content="<h2>SendGrid Test</h2><p>This is a test email from your server.</p>"
                    )
                    
                    sg = SendGridAPIClient(api_key=api_key)
                    response = sg.send(message)
                    
                    if response.status_code == 202:
                        print("✓ Test email sent successfully!")
                        print(f"Check your email: {test_email}")
                    else:
                        print(f"✗ Test email failed with status: {response.status_code}")
                        
                except Exception as e:
                    print(f"✗ Test email error: {e}")
    else:
        print()
        print("Configuration has issues. Please check:")
        print("1. SendGrid API key in .env file")
        print("2. From email in .env file")
        print("3. SendGrid package installation")

if __name__ == "__main__":
    main() 