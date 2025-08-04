#!/usr/bin/env python3
"""
Simple Gmail SMTP test
"""

import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

def test_gmail_smtp():
    """Test Gmail SMTP connection"""
    print("=== Simple Gmail SMTP Test ===")
    
    # Get settings
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    
    print(f"Server: {smtp_server}")
    print(f"Port: {smtp_port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print()
    
    if not username or not password:
        print("✗ Gmail credentials not configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # Send to yourself for testing
        msg['Subject'] = "Gmail SMTP Test"
        
        body = """
        <html>
        <body>
            <h2>Gmail SMTP Test</h2>
            <p>This is a test email sent via Gmail SMTP.</p>
            <p>If you receive this, Gmail SMTP is working correctly!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to Gmail
        print("Connecting to Gmail SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        
        print("Starting TLS...")
        server.starttls()
        
        print("Logging in...")
        server.login(username, password)
        
        print("Sending test email...")
        text = msg.as_string()
        server.sendmail(username, username, text)
        
        print("✓ Test email sent successfully!")
        print(f"Check your Gmail inbox: {username}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("Make sure you're using a Gmail App Password, not your regular password")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_gmail_smtp() 