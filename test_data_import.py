import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1/data-management"

def test_import_all_data():
    """Test importing all data from JSON files to database"""
    print("Testing import all data...")
    
    try:
        response = requests.post(f"{BASE_URL}/import-all")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Data imported successfully!")
    except Exception as e:
        print(f"❌ Error importing data: {e}")

def test_get_stats():
    """Test getting import statistics"""
    print("\nTesting get stats...")
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Database Stats: {data.get('database_stats', {})}")
        print(f"JSON File Stats: {data.get('json_file_stats', {})}")
        print("✅ Stats retrieved successfully!")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

if __name__ == "__main__":
    print("🚀 Testing Data Import API...")
    print("=" * 50)
    
    # Test import endpoint
    test_import_all_data()
    
    # Test stats endpoint
    test_get_stats()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!") 