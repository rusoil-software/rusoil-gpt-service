import os
import json
import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ['MODE'] = 'test'
os.environ['AUTH_SECRET'] = 'test-secret-key-change-in-production'
os.environ['ADMIN_PASSWORD'] = 'test-admin-password'

from backend.app.main import app

client = TestClient(app)


def get_auth_token():
    """
    Helper function to get JWT token for authenticated requests.
    """
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_models_endpoint_unauthorized():
    """
    Test that /api/v1/models requires authentication.
    """
    response = client.get("/api/v1/models")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated - missing Authorization header"

def test_models_endpoint_authorized():
    """
    Test that /api/v1/models works with valid token.
    """
    token = get_auth_token()
    
    response = client.get(
        "/api/v1/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # If models exist, verify structure
    if len(data) > 0:
        model = data[0]
        assert "name" in model
        assert "path" in model
        assert "quantized" in model
        assert "size" in model
        assert "loaded" in model

def test_model_detail_endpoint_unauthorized():
    """
    Test that /api/v1/models/{name} requires authentication.
    """
    response = client.get("/api/v1/models/test-model.ggml")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated - missing Authorization header"

def test_model_detail_endpoint_authorized():
    """
    Test that /api/v1/models/{name} works with valid token.
    """
    token = get_auth_token()
    
    # First get list of models to find a valid name
    models_response = client.get(
        "/api/v1/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if models_response.status_code != 200 or len(models_response.json()) == 0:
        pytest.skip("No models available for testing")
    
    model_name = models_response.json()[0]["name"]
    
    response = client.get(
        f"/api/v1/models/{model_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "path" in data
    assert "quantized" in data
    assert "size_bytes" in data
    assert "created_at" in data

def test_public_endpoints_still_accessible():
    """
    Test that public endpoints (/health, /metrics) remain accessible without authentication.
    """
    # Test /health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    
    # Test /ready endpoint
    response = client.get("/ready")
    assert response.status_code == 200 or response.status_code == 503  # ready may be 503 depending on config
    
    # Test /metrics endpoint
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "petra_health_checks_total" in response.text

def test_invalid_token_access():
    """
    Test that endpoints reject requests with invalid tokens.
    """
    # Try to access protected endpoint with invalid token
    response = client.get(
        "/api/v1/models",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid or expired token"
    
    # Try with malformed token
    response = client.get(
        "/api/v1/models",
        headers={"Authorization": "Bearer"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid authorization header format"

def test_expired_token_access():
    """
    Test that endpoints reject requests with expired tokens.
    """
    from backend.app.auth.security import create_access_token
    
    # Create token that expires immediately
    token = create_access_token(
        data={"sub": "1", "username": "admin"},
        expires_delta=0  # Expired
    )
    
    response = client.get(
        "/api/v1/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid or expired token"

def test_missing_authorization_header():
    """
    Test that endpoints reject requests without Authorization header.
    """
    # Try to access protected endpoint without Authorization header
    response = client.get("/api/v1/models")
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated - missing Authorization header"
    
    # Try with empty Authorization header
    response = client.get(
        "/api/v1/models",
        headers={"Authorization": ""}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid authorization header format"