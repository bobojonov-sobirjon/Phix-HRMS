#!/usr/bin/env python3
"""
Test different SMTP connection methods to bypass firewall restrictions
"""

import socket
import smtplib
import ssl
from datetime import datetime

def test_smtp_methods():
    """Test different SMTP connection methods"""
    print("=== SMTP Connection Method Test ===")
    print(f"Test time: {datetime.now()}")
    print()
    
    # Test different connection methods
    methods = [
        {
            "name": "Gmail SSL (465)",
            "server": "smtp.gmail.com",
            "port": 465,
            "use_ssl": True,
            "use_starttls": False
        },
        {
            "name": "Gmail TLS (587)",
            "server": "smtp.gmail.com", 
            "port": 587,
            "use_ssl": False,
            "use_starttls": True
        },
        {
            "name": "Gmail Plain (587)",
            "server": "smtp.gmail.com",
            "port": 587,
            "use_ssl": False,
            "use_starttls": False
        }
    ]
    
    for method in methods:
        print(f"Testing {method['name']}...")
        
        try:
            # Test basic connection first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((method['server'], method['port']))
            sock.close()
            
            if result == 0:
                print(f"✓ Port {method['port']} is reachable")
                
                # Try SMTP connection
                try:
                    if method['use_ssl']:
                        server = smtplib.SMTP_SSL(method['server'], method['port'], timeout=10)
                        print("✓ SSL connection established")
                    else:
                        server = smtplib.SMTP(method['server'], method['port'], timeout=10)
                        print("✓ Connection established")
                        
                        if method['use_starttls']:
                            server.starttls()
                            print("✓ TLS started")
                    
                    print("✓ SMTP connection successful")
                    server.quit()
                    
                except Exception as e:
                    print(f"✗ SMTP connection failed: {e}")
                    
            else:
                print(f"✗ Port {method['port']} is not reachable (error code: {result})")
                
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
        
        print()

if __name__ == "__main__":
    test_smtp_methods() 