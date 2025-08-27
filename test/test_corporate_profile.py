import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models.corporate_profile import CorporateProfile
from app.models.user import User
from app.utils.auth import create_access_token

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        name="Test User",
        email="test@example.com",
        is_active=True,
        is_verified=True
    )
    user.set_password("testpassword123")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    access_token = create_access_token(data={"sub": test_user.email, "id": test_user.id})
    return {"Authorization": f"Bearer {access_token}"}

def test_create_corporate_profile(auth_headers, test_user):
    """Test creating a corporate profile"""
    profile_data = {
        "company_name": "Test Company",
        "industry": "Technology",
        "phone_number": "1234567890",
        "country_code": "+1",
        "location": "New York",
        "overview": "A test company for testing purposes",
        "website_url": "https://testcompany.com",
        "company_size": "10-50"
    }
    
    response = client.post("/api/v1/corporate-profile/", json=profile_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "profile_id" in data["data"]

def test_create_duplicate_corporate_profile(auth_headers, test_user):
    """Test that user cannot create multiple corporate profiles"""
    profile_data = {
        "company_name": "Test Company 2",
        "industry": "Technology",
        "phone_number": "0987654321",
        "country_code": "+1",
        "location": "Los Angeles",
        "overview": "Another test company",
        "company_size": "50-200"
    }
    
    # First profile should succeed
    response = client.post("/api/v1/corporate-profile/", json=profile_data, headers=auth_headers)
    assert response.status_code == 200
    
    # Second profile should fail
    response = client.post("/api/v1/corporate-profile/", json=profile_data, headers=auth_headers)
    assert response.status_code == 400
    assert "already has a corporate profile" in response.json()["detail"]

def test_get_corporate_profiles():
    """Test getting all corporate profiles"""
    response = client.get("/api/v1/corporate-profile/")
    assert response.status_code == 200
    data = response.json()
    assert "corporate_profiles" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data

def test_get_active_corporate_profiles():
    """Test getting only active corporate profiles"""
    response = client.get("/api/v1/corporate-profile/active")
    assert response.status_code == 200
    data = response.json()
    assert "corporate_profiles" in data

def test_get_corporate_profile_by_id(auth_headers, test_user):
    """Test getting corporate profile by ID"""
    # First create a profile
    profile_data = {
        "company_name": "Test Company 3",
        "industry": "Finance",
        "phone_number": "5555555555",
        "country_code": "+1",
        "location": "Chicago",
        "overview": "A finance company",
        "company_size": "200-1000"
    }
    
    create_response = client.post("/api/v1/corporate-profile/", json=profile_data, headers=auth_headers)
    profile_id = create_response.json()["data"]["profile_id"]
    
    # Then get it by ID
    response = client.get(f"/api/v1/corporate-profile/{profile_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Test Company 3"

def test_get_my_corporate_profile(auth_headers, test_user):
    """Test getting current user's corporate profile"""
    response = client.get("/api/v1/corporate-profile/user/me", headers=auth_headers)
    # Should return 404 if no profile exists
    assert response.status_code == 404

def test_update_corporate_profile(auth_headers, test_user):
    """Test updating corporate profile"""
    # First create a profile
    profile_data = {
        "company_name": "Test Company 4",
        "industry": "Healthcare",
        "phone_number": "1111111111",
        "country_code": "+1",
        "location": "Boston",
        "overview": "A healthcare company",
        "company_size": "1000+"
    }
    
    create_response = client.post("/api/v1/corporate-profile/", json=profile_data, headers=auth_headers)
    profile_id = create_response.json()["data"]["profile_id"]
    
    # Update the profile
    update_data = {
        "company_name": "Updated Company Name",
        "industry": "Updated Industry"
    }
    
    response = client.put(f"/api/v1/corporate-profile/{profile_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Updated Company Name"
    assert data["industry"] == "Updated Industry"

def test_delete_corporate_profile(auth_headers, test_user):
    """Test deleting corporate profile"""
    # First create a profile
    profile_data = {
        "company_name": "Test Company 5",
        "industry": "Education",
        "phone_number": "2222222222",
        "country_code": "+1",
        "location": "San Francisco",
        "overview": "An education company",
        "company_size": "1-10"
    }
    
    create_response = client.post("/api/v1/corporate-profile/", json=profile_data, headers=auth_headers)
    profile_id = create_response.json()["data"]["profile_id"]
    
    # Delete the profile
    response = client.delete(f"/api/v1/corporate-profile/{profile_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

def test_verify_corporate_profile(auth_headers, test_user):
    """Test verifying corporate profile with OTP"""
    # This test would require mocking the OTP system
    # For now, we'll just test the endpoint structure
    verification_data = {
        "otp_code": "123456"
    }
    
    response = client.post("/api/v1/corporate-profile/verify", json=verification_data, headers=auth_headers)
    # Should return 400 for invalid OTP
    assert response.status_code == 400
