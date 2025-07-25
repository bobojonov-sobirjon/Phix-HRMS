#!/usr/bin/env python3
"""
Email setup and authentication test script
This script helps configure email settings and test authentication
"""

import os
import requests
import json

# Email configuration
EMAIL = "sobirbobojonov2000@gmail.com"
PASSWORD = "deellqvxvnehcqba"  # Gmail App Password
BASE_URL = "http://localhost:8000/api/v1/auth"

def create_env_file():
    """Create or update .env file with proper configuration"""
    print("🔧 Setting up environment configuration...")
    
    env_content = f"""# Database Configuration
DATABASE_URL=postgresql://postgres:0576@localhost:5432/phix_hrms

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-2024
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration for OTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME={EMAIL}
SMTP_PASSWORD={PASSWORD}

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
        print("✅ .env file created/updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_email_configuration():
    """Test email configuration"""
    print("\n📧 Testing email configuration...")
    
    # Test SMTP connection
    try:
        import smtplib
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        print("✅ Gmail SMTP connection successful!")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Gmail SMTP connection failed: {e}")
        print("\n⚠️  Note: You may need to:")
        print("1. Enable 2-factor authentication on your Gmail account")
        print("2. Generate an App Password for this application")
        print("3. Use the App Password instead of your regular password")
        return False

def test_authentication():
    """Test authentication endpoints"""
    print("\n🔐 Testing authentication...")
    
    # Test registration
    print("1. Testing user registration...")
    register_data = {
        "name": "Sobir Bobojonov",
        "email": EMAIL,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("token", {}).get("access_token")
            print("   ✅ Registration successful!")
            return token
        elif response.status_code == 400:
            print("   ℹ️  User already exists, trying login...")
            return test_login()
        else:
            print(f"   ❌ Registration failed: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_login():
    """Test user login"""
    print("2. Testing user login...")
    
    login_data = {
        "email": EMAIL,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("token", {}).get("access_token")
            print("   ✅ Login successful!")
            return token
        else:
            print(f"   ❌ Login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_me_endpoint(token):
    """Test /me endpoint with token"""
    print("3. Testing /me endpoint...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("   ✅ /me endpoint successful!")
            print(f"   User: {user_data.get('name')} ({user_data.get('email')})")
            return True
        else:
            print(f"   ❌ /me endpoint failed: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_forgot_password():
    """Test forgot password functionality"""
    print("4. Testing forgot password...")
    
    forgot_data = {
        "email": EMAIL
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forgot-password", json=forgot_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Forgot password email sent!")
            return True
        else:
            print(f"   ❌ Forgot password failed: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Phix HRMS with your credentials")
    print("=" * 60)
    
    # Step 1: Create .env file
    if not create_env_file():
        return
    
    # Step 2: Test email configuration
    test_email_configuration()
    
    # Step 3: Test authentication
    token = test_authentication()
    
    if token:
        print(f"\n✅ Got valid token: {token[:50]}...")
        
        # Step 4: Test /me endpoint
        test_me_endpoint(token)
        
        # Step 5: Test forgot password
        test_forgot_password()
        
        print(f"\n🎉 Setup completed!")
        print(f"\n📋 Summary:")
        print(f"   Email: {EMAIL}")
        print(f"   Token: {token[:50]}...")
        print(f"\n🔗 API Endpoints:")
        print(f"   Register: POST {BASE_URL}/register")
        print(f"   Login: POST {BASE_URL}/login")
        print(f"   Get User: GET {BASE_URL}/me")
        print(f"   Forgot Password: POST {BASE_URL}/forgot-password")
        
        print(f"\n📝 Usage in Postman/API Client:")
        print(f"   URL: GET {BASE_URL}/me")
        print(f"   Headers: Authorization: Bearer {token}")
    else:
        print("\n❌ Failed to get valid token")

if __name__ == "__main__":
    main() 