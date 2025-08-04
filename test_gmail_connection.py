#!/usr/bin/env python3
"""
Test Gmail SMTP connection specifically
"""

import smtplib
import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gmail_connection():
    """Test Gmail SMTP connection"""
    print("=== Gmail Connection Test ===")
    print()
    
    # Get Gmail settings
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print()
    
    if not username or not password:
        print("✗ Gmail credentials not configured")
        print("Please set SMTP_USERNAME and SMTP_PASSWORD in your .env file")
        return False
    
    # Test 1: DNS Resolution
    print("1. Testing DNS resolution...")
    try:
        ip = socket.gethostbyname(smtp_server)
        print(f"✓ DNS resolved: {smtp_server} -> {ip}")
    except socket.gaierror as e:
        print(f"✗ DNS failed: {e}")
        return False
    
    # Test 2: Port Connectivity
    print("2. Testing port connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((smtp_server, smtp_port))
        sock.close()
        
        if result == 0:
            print(f"✓ Port {smtp_port} is reachable")
        else:
            print(f"✗ Port {smtp_port} is not reachable (error code: {result})")
            print("This means your cloud provider is blocking SMTP ports")
            return False
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False
    
    # Test 3: SMTP Connection
    print("3. Testing SMTP connection...")
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        print("✓ SMTP connection established")
        
        server.starttls()
        print("✓ TLS started")
        
        server.login(username, password)
        print("✓ Gmail authentication successful")
        
        server.quit()
        print("✓ Gmail connection test completed successfully")
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

def test_gmail_email_send():
    """Test sending a test email via Gmail"""
    print()
    print("=== Gmail Email Send Test ===")
    
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME", "")
        password = os.getenv("SMTP_PASSWORD", "")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # Send to yourself for testing
        msg['Subject'] = "Gmail Test Email"
        
        body = """
        <html>
        <body>
            <h2>Gmail Test Email</h2>
            <p>This is a test email sent from your server via Gmail SMTP.</p>
            <p>If you receive this, Gmail is working correctly!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(username, password)
        
        text = msg.as_string()
        server.sendmail(username, username, text)
        server.quit()
        
        print("✓ Test email sent successfully!")
        print(f"Check your Gmail inbox: {username}")
        return True
        
    except Exception as e:
        print(f"✗ Test email failed: {e}")
        return False

def main():
    print("Testing Gmail configuration...")
    print()
    
    if test_gmail_connection():
        print()
        print("Gmail connection is working!")
        print()
        
        # Ask if user wants to test sending
        test_send = input("Do you want to test sending an email? (y/n): ").strip().lower()
        if test_send == 'y':
            test_gmail_email_send()
    else:
        print()
        print("Gmail connection failed. Please check:")
        print("1. Gmail credentials in .env file")
        print("2. Gmail App Password (not regular password)")
        print("3. Cloud provider firewall settings")
        print("4. Network connectivity")

if __name__ == "__main__":
    main() 