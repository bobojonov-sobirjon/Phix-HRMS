import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"

def test_login_user():
    """Test user login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data

def test_forgot_password():
    """Test forgot password OTP request"""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "test@example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["email"] == "test@example.com"

def test_invalid_login():
    """Test invalid login credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_duplicate_registration():
    """Test duplicate user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400

if __name__ == "__main__":
    pytest.main([__file__]) 