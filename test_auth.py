#!/usr/bin/env python3
"""
Test authentication script
This script helps test the authentication endpoints
"""

import requests
import json
from datetime import datetime

# Base URL for your API
BASE_URL = "http://localhost:8000/api/v1/auth"

def test_register():
    """Test user registration"""
    print("🔍 Testing user registration...")
    
    data = {
        "name": "Sobir Bobojonov",
        "email": "sobirbobojonov2000@gmail.com",
        "password": "deellqvxvnehcqba"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json().get("token", {}).get("access_token")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_login():
    """Test user login"""
    print("\n🔍 Testing user login...")
    
    data = {
        "email": "sobirbobojonov2000@gmail.com",
        "password": "deellqvxvnehcqba"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json().get("token", {}).get("access_token")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_me(token):
    """Test getting current user info"""
    print(f"\n🔍 Testing /me endpoint with token...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_token_generation():
    """Test token generation endpoint"""
    print("\n🔍 Testing token generation...")
    
    try:
        response = requests.post(f"{BASE_URL}/test-token")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json().get("token")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def decode_token(token):
    """Decode JWT token to see its contents"""
    print(f"\n🔍 Decoding token...")
    try:
        import jwt
        from app.config import settings
        
        # Decode without verification to see the payload
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"Token payload: {json.dumps(payload, indent=2, default=str)}")
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            now = datetime.utcnow()
            if exp_time < now:
                print("❌ Token is expired!")
            else:
                print(f"✅ Token is valid until: {exp_time}")
        
        return payload
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Testing Phix HRMS Authentication API")
    print("=" * 50)
    
    # Test 1: Register a new user
    token = test_register()
    
    if not token:
        # Test 2: Try to login
        token = test_login()
    
    if not token:
        # Test 3: Generate a test token
        token = test_token_generation()
    
    if token:
        print(f"\n✅ Got token: {token[:50]}...")
        
        # Decode the token
        decode_token(token)
        
        # Test 4: Use the token to get user info
        test_get_me(token)
    else:
        print("\n❌ Failed to get a valid token")

if __name__ == "__main__":
    main() 