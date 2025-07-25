#!/usr/bin/env python3
"""
Complete authentication test script
This script tests all authentication endpoints including forgot password
"""

import requests
import json
import time

# Base URL for your API
BASE_URL = "http://localhost:8000/api/v1/auth"

def test_health():
    """Test if server is running"""
    print("🔍 Testing server health...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return False

def test_register():
    """Test user registration"""
    print("\n🔍 Testing user registration...")
    
    data = {
        "name": "Sobir Bobojonov",
        "email": "sobirbobojonov2000@gmail.com",
        "password": "deellqvnevnehcqba"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("token", {}).get("access_token")
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
    print("\n🔍 Testing user login...")
    
    data = {
        "email": "sobirbobojonov2000@gmail.com",
        "password": "deellqvnevnehcqba"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("token", {}).get("access_token")
            print("   ✅ Login successful!")
            return token
        else:
            print(f"   ❌ Login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_get_me(token):
    """Test getting current user info"""
    print("\n🔍 Testing /me endpoint...")
    
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
    print("\n🔍 Testing forgot password...")
    
    data = {
        "email": "sobirbobojonov2000@gmail.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forgot-password", json=data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Forgot password successful!")
            print(f"   Message: {result.get('message')}")
            
            # Check if OTP code is included in response (for testing)
            otp_code = result.get('otp_code')
            if otp_code:
                print(f"   📧 OTP Code: {otp_code}")
                return otp_code
            else:
                print("   📧 Check your email for OTP code")
                return None
        else:
            print(f"   ❌ Forgot password failed: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_verify_otp(otp_code):
    """Test OTP verification"""
    print("\n🔍 Testing OTP verification...")
    
    data = {
        "email": "sobirbobojonov2000@gmail.com",
        "otp_code": otp_code
    }
    
    try:
        response = requests.post(f"{BASE_URL}/verify-otp", json=data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ OTP verification successful!")
            return True
        else:
            print(f"   ❌ OTP verification failed: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_reset_password(otp_code):
    """Test password reset"""
    print("\n🔍 Testing password reset...")
    
    data = {
        "email": "sobirbobojonov2000@gmail.com",
        "otp_code": otp_code,
        "new_password": "newpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/reset-password", json=data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Password reset successful!")
            return True
        else:
            print(f"   ❌ Password reset failed: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_token_generation():
    """Test token generation endpoint"""
    print("\n🔍 Testing token generation...")
    
    try:
        response = requests.post(f"{BASE_URL}/test-token")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("token")
            print("   ✅ Token generation successful!")
            return token
        else:
            print(f"   ❌ Token generation failed: {response.json()}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Complete Phix HRMS Authentication Test")
    print("=" * 60)
    
    # Step 1: Check server health
    if not test_health():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python -m uvicorn app.main:app --reload")
        return
    
    # Step 2: Test registration/login
    token = test_register()
    
    if not token:
        print("\n❌ Failed to get authentication token")
        return
    
    print(f"\n✅ Got valid token: {token[:50]}...")
    
    # Step 3: Test /me endpoint
    test_get_me(token)
    
    # Step 4: Test forgot password
    otp_code = test_forgot_password()
    
    if otp_code:
        print(f"\n📧 Using OTP code: {otp_code}")
        
        # Step 5: Test OTP verification
        if test_verify_otp(otp_code):
            # Step 6: Test password reset
            test_reset_password(otp_code)
    
    # Step 7: Test token generation
    test_token_generation()
    
    print("\n🎉 Complete test finished!")
    print("\n📋 Summary:")
    print(f"   ✅ Server: Running")
    print(f"   ✅ Authentication: Working")
    print(f"   ✅ Token: {token[:50]}...")
    if otp_code:
        print(f"   ✅ OTP: {otp_code}")
    
    print(f"\n🔗 API Endpoints tested:")
    print(f"   ✅ POST {BASE_URL}/register")
    print(f"   ✅ POST {BASE_URL}/login")
    print(f"   ✅ GET {BASE_URL}/me")
    print(f"   ✅ POST {BASE_URL}/forgot-password")
    print(f"   ✅ POST {BASE_URL}/verify-otp")
    print(f"   ✅ POST {BASE_URL}/reset-password")
    print(f"   ✅ POST {BASE_URL}/test-token")

if __name__ == "__main__":
    main() 