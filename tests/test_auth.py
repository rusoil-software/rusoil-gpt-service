import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Set test environment before importing app
os.environ['MODE'] = 'test'
os.environ['AUTH_SECRET'] = 'test-secret-key-change-in-production'
os.environ['ADMIN_PASSWORD'] = 'test-admin-password'

from backend.app.main import app

client = TestClient(app)


def test_login_success():
    """
    Test successful login with valid credentials.
    """
    # First, ensure admin user is created
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

def test_login_invalid_username():
    """
    Test login with invalid username.
    """
    response = client.post(
        "/auth/login",
        data={"username": "invalid", "password": "test-admin-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_login_invalid_password():
    """
    Test login with invalid password.
    """
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "invalid-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_login_missing_credentials():
    """
    Test login with missing credentials.
    """
    response = client.post(
        "/auth/login",
        data={},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Should return 422 for validation error
    assert response.status_code == 422

def test_get_me_unauthorized():
    """
    Test accessing /auth/me without authentication.
    """
    response = client.get("/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

def test_get_me_authorized():
    """
    Test accessing /auth/me with valid token.
    Verifies that the JWT middleware properly authenticates and provides user data.
    """
    # First get token
    login_response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["is_admin"] is True
    assert "id" in data
    assert "is_active" in data
    
    # Verify user is available in request state (middleware functionality)
    assert hasattr(client.app.state, 'user')
    assert client.app.state.user.username == "admin"

def test_get_me_invalid_token():
    """
    Test accessing /auth/me with invalid token.
    """
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid or expired token"

def test_get_me_expired_token():
    """
    Test accessing /auth/me with expired token.
    """
    from backend.app.auth.security import create_access_token
    
    # Create token that expires in 1 second
    token = create_access_token(
        data={"sub": "1", "username": "test"},
        expires_delta=1
    )
    
    # Wait for token to expire
    import time
    time.sleep(2)
    
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid or expired token"

def test_admin_initialization():
    """
    Test that admin user is initialized on startup.
    """
    # Check if users.json was created
    import os
    from backend.app.auth.users import _users
    
    assert os.path.exists("backend/app/auth/users.json")
    assert len(_users) > 0
    assert _users[1].username == "admin"
    assert _users[1].is_admin is True

def test_password_hashing():
    """
    Test that passwords are properly hashed and verified.
    """
    from backend.app.auth.security import Hasher
    
    password = "test-password"
    hashed = Hasher.get_password_hash(password)
    
    assert hashed != password  # Password is hashed
    assert Hasher.verify_password(password, hashed) is True  # Can verify
    assert Hasher.verify_password("wrong-password", hashed) is False  # Rejects wrong password

def test_jwt_token_creation():
    """
    Test JWT token creation and decoding.
    """
    from backend.app.auth.security import create_access_token, decode_access_token
    
    # Create token
    data = {"sub": "123", "username": "testuser"}
    token = create_access_token(data=data, expires_delta=300)  # 5 minutes
    
    # Decode token
    payload = decode_access_token(token)
    
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["username"] == "testuser"
    assert "exp" in payload

def test_inactive_user():
    """
    Test that inactive users cannot login.
    """
    from backend.app.auth.users import create_user, get_user_by_username
    from backend.app.auth.security import get_password_hash
    
    # Create inactive user
    hashed_password = get_password_hash("test-password")
    user = create_user("inactive", hashed_password)
    user.is_active = False
    
    # Try to login
    response = client.post(
        "/auth/login",
        data={"username": "inactive", "password": "test-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Inactive user"

def test_case_insensitive_username():
    """
    Test that username lookup is case-insensitive.
    """
    from backend.app.auth.users import create_user, get_user_by_username
    from backend.app.auth.security import get_password_hash
    
    # Create user with mixed case
    hashed_password = get_password_hash("test-password")
    create_user("TestUser", hashed_password)
    
    # Look up with different cases
    user1 = get_user_by_username("testuser")
    user2 = get_user_by_username("TESTUSER")
    user3 = get_user_by_username("TestUser")
    
    assert user1 is not None
    assert user2 is not None
    assert user3 is not None
    assert user1.id == user2.id == user3.id