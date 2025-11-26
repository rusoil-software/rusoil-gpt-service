Petra is a Dockerized GPT Service developed in Ufa State Petroleum Technological University

## Authentication

The service implements JWT-based authentication to secure API endpoints. All endpoints except `/health` and `/metrics` require authentication.

### Getting Started with Authentication

1. **Set environment variables**:
```bash
# Required for authentication
export AUTH_SECRET="your-super-secret-key-change-in-production"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="secure-admin-password"

# Optional: authentication disabled in local mode for development
export MODE="local"  # Remove this for production
```

2. **Start the service**:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

3. **Log in to get JWT token**:
```bash
# Using form data
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=secure-admin-password"

# Using JSON
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure-admin-password"}'
```

4. **Call protected endpoints with JWT**:
```bash
# Store token (replace with actual token from login response)
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Call protected endpoint (list models)
curl -X GET "http://localhost:8000/api/v1/models" \
  -H "Authorization: Bearer $TOKEN"

# Get current user information
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Example Workflows

**Complete authentication workflow**:
```bash
# 1. Set environment
export AUTH_SECRET="test-secret"
export ADMIN_PASSWORD="admin123"

# 2. Start server in background
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &

# 3. Wait for server to start
sleep 3

# 4. Login and capture token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin123" | jq -r '.access_token')

# 5. Use token to access protected endpoint
curl -X GET "http://localhost:8000/api/v1/models" \
  -H "Authorization: Bearer $TOKEN"

# 6. Check current user
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# 7. Stop server
kill %1
```

**Error handling examples**:
```bash
# Invalid credentials
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=wrong-password"
# Returns: {"detail": "Incorrect username or password"}

# Missing token
curl -X GET "http://localhost:8000/api/v1/models"
# Returns: {"detail": "Not authenticated - missing Authorization header"}

# Invalid token
curl -X GET "http://localhost:8000/api/v1/models" \
  -H "Authorization: Bearer invalid-token"
# Returns: {"detail": "Invalid or expired token"}
```

Short pointer:

- Conventions: see `doc/conventions.md` for the concise contributor checklist and rules.

See `doc/vision.md` for the living technical blueprint and rationale.


API docs: see `docs/api.md` for quick examples and environment variables. The interactive OpenAPI docs are available at `/docs` when the backend is running.

