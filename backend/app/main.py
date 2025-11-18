import os
import os.path
import time
from pathlib import Path
from typing import Dict, List
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from werkzeug.utils import secure_filename
# prometheus
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge, REGISTRY

start_time = time.time()
app = FastAPI(title="Petra GPT Service - Backend")

# basic prometheus metrics

def _safe_metric(ctor, name, *args, **kwargs):
    try:
        return ctor(name, *args, **kwargs)
    except ValueError:
        # metric already registered in global registry; try to return existing collector
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is not None:
            return existing
        raise

HEALTH_CHECKS = _safe_metric(Counter, 'petra_health_checks_total', 'Number of health checks')
READY_CHECKS = _safe_metric(Counter, 'petra_ready_checks_total', 'Number of readiness checks')

# HTTP metrics (method+path+status), latency histogram, and model-inference gauge
HTTP_REQUESTS = _safe_metric(Counter, 'http_requests_total', 'HTTP requests', ['method', 'path', 'status'])
HTTP_REQUEST_DURATION = _safe_metric(Histogram, 'http_request_duration_seconds', 'HTTP request duration seconds', ['method', 'path'])
MODEL_INFER_GAUGE = _safe_metric(Gauge, 'model_inference_inprogress', 'In-progress model inference requests')

# Toggle metrics collection via env var
METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'false').lower() in ('1', 'true', 'yes')


def uptime_seconds() -> float:
    return time.time() - start_time


def check_readiness() -> Dict[str, object]:
    """Perform lightweight readiness checks.

    Returns a dict with `ok: bool` and details for diagnostics.
    """
    mode = os.getenv("MODE", "local")
    details = {"mode": mode}

    # In local mode be permissive: process running is fine
    if mode == "local":
        details["db_ok"] = None
        details["indexes_ok"] = None
        return {"ok": True, "details": details}

    # For other modes, assert existence of a DB file and index directory (non-blocking reported)
    db_path = Path(os.getenv("DATABASE_PATH", "data/db.sqlite"))
    index_dir = Path(os.getenv("INDEX_DIR", "data/indexes"))

    details["db_path"] = str(db_path)
    details["index_dir"] = str(index_dir)
    details["db_ok"] = db_path.exists()
    details["indexes_ok"] = index_dir.exists()

    ok = details["db_ok"] and details["indexes_ok"]
    return {"ok": ok, "details": details}


@app.get("/health")
def health():
    HEALTH_CHECKS.inc()
    payload = {
        "status": "ok",
        "uptime": round(uptime_seconds(), 2),
        "version": os.getenv("VERSION", "0.0.0"),
    }
    return JSONResponse(status_code=200, content=payload)


@app.get("/ready")
def ready():
    READY_CHECKS.inc()
    result = check_readiness()
    if result["ok"]:
        return JSONResponse(status_code=200, content={"status": "ready", **result["details"]})
    return JSONResponse(status_code=503, content={"status": "not-ready", **result["details"]})


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not METRICS_ENABLED:
            return await call_next(request)

        method = request.method
        path = request.url.path
        MODEL_INFER_GAUGE.inc(0)
        start = time.time()
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        finally:
            duration = time.time() - start
            try:
                HTTP_REQUESTS.labels(method=method, path=path, status=status).inc()
                HTTP_REQUEST_DURATION.labels(method=method, path=path).observe(duration)
            except Exception:
                # be defensive: metrics instrumentation should not break requests
                pass


if METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)


@app.get("/metrics")
def metrics():
    """Expose Prometheus metrics"""
    data = generate_latest()
    return PlainTextResponse(content=data.decode('utf-8'), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/models")
def list_models() -> List[Dict[str, object]]:
    """List available local models with basic metadata.

    Reads `MODEL_DIR` environment variable (defaults to `models`).
    """
    # Resolve a safe model directory anchored to the repository root.
    repo_root = Path(__file__).resolve().parents[3]
    raw_model_dir = Path(os.getenv('MODEL_DIR', 'models'))
    # If the provided model dir is absolute, resolve it; otherwise consider it relative to the repo root.
    if raw_model_dir.is_absolute():
        model_dir = raw_model_dir.resolve()
    else:
        model_dir = (repo_root / raw_model_dir).resolve()

    # If the provided model dir was absolute, accept it only if it exists and is a directory.
    if raw_model_dir.is_absolute():
        allowed = model_dir.exists() and model_dir.is_dir()
    else:
        # For relative paths enforce they resolve inside the repository root (defense-in-depth).
        try:
            allowed = model_dir.is_relative_to(repo_root)
        except AttributeError:
            allowed = str(model_dir).startswith(str(repo_root))

    if not allowed or not model_dir.exists() or not model_dir.is_dir():
        return []

    def human_size(n: int) -> str:
        # simple human-readable size (K, M, G) following KISS
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if n < 1024.0:
                return f"{n:.0f}{unit}" if unit == 'B' else f"{n:.1f}{unit}"
            n /= 1024.0
        return f"{n:.1f}PB"

    def detect_quantized(fname: str) -> bool:
        # naive detection: common quant markers
        lowered = fname.lower()
        markers = ['.q', 'quant', 'q4_', 'q5_', '.gguf.q']
        return any(m in lowered for m in markers)

    result = []
    for p in sorted(model_dir.iterdir()):
        if p.is_file():
            stat = p.stat()
            relpath = str(p.relative_to(model_dir))
            q = detect_quantized(p.name)
            result.append({
                'name': p.name,
                'path': relpath,
                'quantized': q,
                'size': human_size(stat.st_size),
                'loaded': False,
            })
    return result


@app.get("/api/v1/models/{name}")
def get_model(name: str) -> Dict[str, object]:
    # Combine sanitization and repo-root anchoring to address CodeQL path-expression findings.
    # First, sanitise the filename component using Werkzeug to remove dangerous characters.
    safe_name = secure_filename(name)
    if not safe_name:
        raise HTTPException(status_code=400, detail='invalid model name')

    # Conservative validation: only allow reasonably short filenames after sanitization
    if not re.match(r'^[A-Za-z0-9._-]{1,255}$', safe_name):
        raise HTTPException(status_code=400, detail='invalid model name')

    # Resolve a safe model directory anchored to the repository root (same logic as list_models)
    repo_root = Path(__file__).resolve().parents[3]
    raw_model_dir = Path(os.getenv('MODEL_DIR', 'models'))
    if raw_model_dir.is_absolute():
        model_dir = raw_model_dir.resolve()
    else:
        model_dir = (repo_root / raw_model_dir).resolve()

    if raw_model_dir.is_absolute():
        # allow absolute model dirs if they exist
        allowed = model_dir.exists() and model_dir.is_dir()
    else:
        try:
            allowed = model_dir.is_relative_to(repo_root)
        except AttributeError:
            allowed = str(model_dir).startswith(str(repo_root))

    if not allowed:
        # refuse to operate on externally-controlled model directories (relative values must be inside repo)
        raise HTTPException(status_code=403, detail='model directory not allowed')

    # Construct the absolute, normalized candidate path with sanitized filename
    p = (model_dir / safe_name).resolve()

    # Ensure the resolved path is within the model directory (prevent path traversal)
    try:
        is_subpath = p.is_relative_to(model_dir)
    except AttributeError:
        is_subpath = str(p).startswith(str(model_dir))

    if not is_subpath:
        raise HTTPException(status_code=403, detail='invalid model name')

    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail='model not found')

    stat = p.stat()

    def detect_quant_type(fname: str) -> str:
        lowered = fname.lower()
        if 'q4_0' in lowered:
            return 'q4_0'
        if 'q4_1' in lowered:
            return 'q4_1'
        if 'q5_' in lowered:
            return 'q5'
        if '.gguf.q' in lowered:
            return 'gguf.q'
        if 'quant' in lowered:
            return 'quantized'
        return 'fp32'

    quant_type = detect_quant_type(p.name)

    # recommended loader params (kept minimal and safe)
    loader_params = {
        'threads': int(os.getenv('DEFAULT_THREADS', '4')),
        'n_ctx': int(os.getenv('DEFAULT_N_CTX', '2048')),
    }

    return {
        'name': p.name,
        'path': str(p.relative_to(model_dir)),
        'quantized': quant_type != 'fp32',
        'quant_type': quant_type,
        'loader_params': loader_params,
        'size_bytes': stat.st_size,
        'size': (lambda s: f"{s}B")(stat.st_size),
        'created_at': stat.st_ctime,
        'modified': stat.st_mtime,
        'loaded': False,
    }


@app.get("/")
def index():
    return {"msg": "Petra backend (health endpoints available at /health and /ready)"}
