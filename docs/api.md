# API reference (basic)

This document lists the basic API endpoints for the Petra backend.

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

Environment variables:

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
