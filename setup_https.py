#!/usr/bin/env python3
"""
Setup script for HTTPS configuration
"""

import os
import subprocess
import sys

def check_ssl_certificates():
    """Check if SSL certificates exist"""
    cert_path = "/etc/letsencrypt/live/your-domain.com/fullchain.pem"
    key_path = "/etc/letsencrypt/live/your-domain.com/privkey.pem"
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("✓ SSL certificates found")
        return True
    else:
        print("✗ SSL certificates not found")
        return False

def install_certbot():
    """Install Certbot for SSL certificates"""
    print("Installing Certbot...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "certbot", "python3-certbot-nginx", "-y"], check=True)
        print("✓ Certbot installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Certbot: {e}")
        return False

def generate_ssl_certificate(domain):
    """Generate SSL certificate using Certbot"""
    print(f"Generating SSL certificate for {domain}...")
    try:
        subprocess.run([
            "sudo", "certbot", "certonly", 
            "--standalone", 
            "-d", domain,
            "--non-interactive",
            "--agree-tos",
            "--email", "your-email@example.com"
        ], check=True)
        print("✓ SSL certificate generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate SSL certificate: {e}")
        return False

def setup_nginx_ssl(domain):
    """Setup Nginx with SSL configuration"""
    nginx_config = f"""
server {{
    listen 80;
    server_name {domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl;
    server_name {domain};
    
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    config_path = f"/etc/nginx/sites-available/{domain}"
    try:
        with open(config_path, 'w') as f:
            f.write(nginx_config)
        
        # Enable the site
        subprocess.run(["sudo", "ln", "-sf", config_path, f"/etc/nginx/sites-enabled/{domain}"], check=True)
        subprocess.run(["sudo", "nginx", "-t"], check=True)
        subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
        
        print("✓ Nginx SSL configuration completed")
        return True
    except Exception as e:
        print(f"✗ Failed to setup Nginx SSL: {e}")
        return False

def main():
    print("=== HTTPS Setup Script ===")
    print()
    
    # Get domain from user
    domain = input("Enter your domain name (e.g., yourdomain.com): ").strip()
    if not domain:
        print("✗ Domain name is required")
        return
    
    print(f"Setting up HTTPS for: {domain}")
    print()
    
    # Check if SSL certificates exist
    if not check_ssl_certificates():
        # Install Certbot
        if not install_certbot():
            return
        
        # Generate SSL certificate
        if not generate_ssl_certificate(domain):
            return
    
    # Setup Nginx with SSL
    if not setup_nginx_ssl(domain):
        return
    
    print()
    print("=== HTTPS Setup Complete ===")
    print(f"Your app should now be accessible at: https://{domain}")
    print()
    print("To run your app with HTTPS:")
    print("1. Make sure your app is running on port 9000")
    print("2. Access via https://yourdomain.com")
    print()
    print("Note: The email sending issue is separate from HTTPS setup.")

if __name__ == "__main__":
    main() 