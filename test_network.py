#!/usr/bin/env python3
"""
Simple network connectivity test for SMTP servers
Run this on your server to diagnose email connectivity issues
"""

import socket
import smtplib
import sys
from datetime import datetime

def test_dns(hostname):
    """Test DNS resolution"""
    print(f"Testing DNS resolution for {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✓ DNS resolved: {hostname} -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"✗ DNS failed: {e}")
        return False

def test_port(hostname, port, timeout=10):
    """Test if port is reachable"""
    print(f"Testing connection to {hostname}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Port {port} is reachable")
            return True
        else:
            print(f"✗ Port {port} is not reachable (error code: {result})")
            return False
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False

def test_smtp_connection(hostname, port, username, password):
    """Test SMTP connection and authentication"""
    print(f"Testing SMTP connection to {hostname}:{port}...")
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(hostname, port, timeout=10)
            print("✓ SSL connection established")
        else:
            server = smtplib.SMTP(hostname, port, timeout=10)
            print("✓ Connection established")
            server.starttls()
            print("✓ TLS started")
        
        server.login(username, password)
        print("✓ Authentication successful")
        server.quit()
        print("✓ SMTP test completed successfully")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def main():
    print("=== SMTP Network Connectivity Test ===")
    print(f"Test time: {datetime.now()}")
    print()
    
    # Test Gmail SMTP
    print("1. Testing Gmail SMTP...")
    gmail_host = "smtp.gmail.com"
    
    if test_dns(gmail_host):
        if test_port(gmail_host, 587):
            print("✓ Gmail port 587 is reachable")
        else:
            print("✗ Gmail port 587 is not reachable")
            
        if test_port(gmail_host, 465):
            print("✓ Gmail port 465 is reachable")
        else:
            print("✗ Gmail port 465 is not reachable")
    
    print()
    
    # Test Outlook SMTP
    print("2. Testing Outlook SMTP...")
    outlook_host = "smtp-mail.outlook.com"
    
    if test_dns(outlook_host):
        if test_port(outlook_host, 587):
            print("✓ Outlook port 587 is reachable")
        else:
            print("✗ Outlook port 587 is not reachable")
    
    print()
    
    # Test Yahoo SMTP
    print("3. Testing Yahoo SMTP...")
    yahoo_host = "smtp.mail.yahoo.com"
    
    if test_dns(yahoo_host):
        if test_port(yahoo_host, 587):
            print("✓ Yahoo port 587 is reachable")
        else:
            print("✗ Yahoo port 587 is not reachable")
    
    print()
    print("=== Test Complete ===")
    print()
    print("If ports are not reachable, check:")
    print("1. Server firewall settings")
    print("2. Cloud provider firewall rules")
    print("3. Network configuration")

if __name__ == "__main__":
    main() 