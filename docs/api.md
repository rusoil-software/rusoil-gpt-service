# API reference

This document lists the API endpoints for the Petra backend.

## Health

GET /health

- Summary: Liveness / health check
- Example:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","uptime":12.3,"version":"0.0.0"}
```

## Readiness

GET /ready

- Summary: Readiness check

## Metrics

GET /metrics

- Summary: Prometheus metrics (read-only)
- Example:

```bash
curl http://127.0.0.1:8000/metrics
# # HELP petra_health_checks_total Number of health checks
# petra_health_checks_total 1
```

## Authentication

POST /auth/login

- Summary: Authenticate user and return JWT access token
- Parameters:
  - username: User's username
  - password: User's password
- Example:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=your-password"
# {"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer"}
```

GET /auth/me

- Summary: Get current authenticated user's information
- Requires: Bearer token in Authorization header
- Example:

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
# {"id": 1, "username": "admin", "is_active": true, "is_admin": true}
```

Environment variables:

- `AUTH_SECRET` - Secret key for signing JWT tokens (required for production)
- `ADMIN_USERNAME` - Username for admin account (default: admin)
- `ADMIN_PASSWORD` - Password for admin account (required to create admin user)
- `METRICS_ENABLED` - set to `true` to enable metrics middleware and expose `/metrics`.
- `MODE` - `local` or `prod` changes readiness checks behavior.

## Models API

GET /api/v1/models

- Summary: List available models
- Example:

```bash
curl http://127.0.0.1:8000/api/v1/models
# [{"name":"model.ggml","path":"model.ggml","quantized":false,"size":"1KB","loaded":false}]
```

GET /api/v1/models/{name}

- Summary: Get detailed metadata for a model
- Example:

```bash
curl http://127.0.0.1:8000/api/v1/models/model.ggml
# {"name":"model.ggml","path":"model.ggml","quantized":true,"quant_type":"q4_0","loader_params":{"threads":4,"n_ctx":2048}}
```
