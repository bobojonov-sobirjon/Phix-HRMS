"""
Test script for corporate profile creation endpoint
Bu test fayli corporate profile yaratish endpoint'ini tekshiradi.
"""
import requests
import json
from io import BytesIO

# Test configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"
# Token'ni o'zgartiring
AUTH_TOKEN = "YOUR_TOKEN_HERE"

def print_separator():
    """Print separator line"""
    print("\n" + "=" * 60 + "\n")

def test_create_corporate_profile_without_logo():
    """Test creating corporate profile without logo"""
    url = f"{BASE_URL}/corporate-profile/"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    data = {
        "company_name": "Test Company",
        "phone_number": "1234567890",
        "country_code": "+1",
        "location_id": 1,
        "overview": "This is a test company overview",
        "website_url": "https://test.com",
        "company_size": "1-10",
        "category_id": None
    }
    
    print("Testing corporate profile creation without logo...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_create_corporate_profile_with_empty_logo_string():
    """Test creating corporate profile with empty logo string"""
    url = f"{BASE_URL}/corporate-profile/"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    data = {
        "company_name": "Test Company 2",
        "phone_number": "1234567891",
        "country_code": "+1",
        "location_id": 1,
        "overview": "This is a test company overview 2",
        "website_url": "https://test2.com",
        "company_size": "1-10",
        "category_id": None,
        "logo": ""  # Empty string
    }
    
    print("\n\nTesting corporate profile creation with empty logo string...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_create_corporate_profile_with_logo_file():
    """Test creating corporate profile with logo file"""
    url = f"{BASE_URL}/corporate-profile/"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    data = {
        "company_name": "Test Company 3",
        "phone_number": "1234567892",
        "country_code": "+1",
        "location_id": 1,
        "overview": "This is a test company overview 3",
        "website_url": "https://test3.com",
        "company_size": "1-10",
        "category_id": None
    }
    
    # Create a dummy image file
    files = {
        "logo": ("test_logo.jpg", BytesIO(b"fake image content"), "image/jpeg")
    }
    
    print("\n\nTesting corporate profile creation with logo file...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, data=data, files=files, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Corporate Profile Creation Test")
    print("=" * 60)
    print("\nNOTE: Please update AUTH_TOKEN with a valid authentication token")
    print("=" * 60)
    
    if AUTH_TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set AUTH_TOKEN before running tests!")
        print("You can get a token by logging in through the auth endpoint.")
        print("\nExample:")
        print("  AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'")
    else:
        # Run tests
        print_separator()
        test1 = test_create_corporate_profile_without_logo()
        print_separator()
        test2 = test_create_corporate_profile_with_empty_logo_string()
        print_separator()
        test3 = test_create_corporate_profile_with_logo_file()
        
        print("\n" + "=" * 60)
        print("Test Results:")
        print("=" * 60)
        print(f"Test 1 (without logo): {'✅ PASSED' if test1 else '❌ FAILED'}")
        print(f"Test 2 (empty logo string): {'✅ PASSED' if test2 else '❌ FAILED'}")
        print(f"Test 3 (with logo file): {'✅ PASSED' if test3 else '❌ FAILED'}")
        print("=" * 60)
        
        if all([test1, test2, test3]):
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed. Please check the output above.")
