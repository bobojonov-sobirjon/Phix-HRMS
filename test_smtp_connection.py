#!/usr/bin/env python3
"""
Test SMTP connection to Gmail servers
"""
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection(server, port, use_ssl=False):
    """Test SMTP connection"""
    print(f"\n=== Testing {server}:{port} (SSL: {use_ssl}) ===")
    
    try:
        # Test basic socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((server, port))
        sock.close()
        
        if result != 0:
            print(f"❌ Socket connection failed: {result}")
            return False
        
        print(f"✅ Socket connection successful")
        
        # Test SMTP connection
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.starttls()
        
        print(f"✅ SMTP connection successful")
        
        # Try to login (this will fail without proper credentials, but we can see if connection works)
        try:
            smtp.login("test@test.com", "test")
        except smtplib.SMTPAuthenticationError:
            print("✅ SMTP authentication test (expected to fail with test credentials)")
        except Exception as e:
            print(f"⚠️  SMTP login test: {e}")
        
        smtp.quit()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    print("Testing SMTP connections to Gmail servers...")
    
    # Test different configurations
    configs = [
        ("smtp.gmail.com", 465, True),   # SSL
        ("smtp.gmail.com", 587, False),  # TLS
        ("smtp.gmail.com", 25, False),   # Standard SMTP
    ]
    
    working_configs = []
    
    for server, port, use_ssl in configs:
        if test_connection(server, port, use_ssl):
            working_configs.append((server, port, use_ssl))
    
    print(f"\n=== RESULTS ===")
    print(f"Working configurations: {len(working_configs)}")
    for server, port, use_ssl in working_configs:
        print(f"✅ {server}:{port} (SSL: {use_ssl})")
    
    if not working_configs:
        print("❌ No working SMTP configurations found!")
        print("This suggests a network/firewall issue at the ISP or cloud provider level.")
    else:
        print(f"\nRecommended configuration:")
        best_config = working_configs[0]
        print(f"SMTP_SERVER={best_config[0]}")
        print(f"SMTP_PORT={best_config[1]}")
        if best_config[2]:
            print("# Use SMTP_SSL=True in your email code")

if __name__ == "__main__":
    main() 