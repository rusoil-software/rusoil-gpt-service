import os
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Depends

start_time = time.time()
app = FastAPI(title="Petra GPT Service - Backend")


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


# -------------------------
# Prometheus metrics setup
# -------------------------
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() in ("1", "true", "yes")

if METRICS_ENABLED:
    REQUEST_COUNT = Counter(
        "petra_http_requests_total", "Total HTTP requests", ["method", "path", "status"]
    )
    REQUEST_LATENCY = Histogram(
        "petra_http_request_latency_seconds", "HTTP request latency seconds", ["method", "path"]
    )
    MODEL_INFER_INPROGRESS = Gauge(
        "petra_model_inference_inprogress", "Number of in-progress model inference requests", ["model"]
    )
    MODEL_INFER_DURATION = Histogram(
        "petra_model_inference_duration_seconds", "Model inference duration seconds", ["model"]
    )


    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        method = request.method
        path = request.url.path
        with REQUEST_LATENCY.labels(method=method, path=path).time():
            resp = await call_next(request)
        try:
            status = str(resp.status_code)
        except Exception:
            status = "500"
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        return resp
else:
    # No-op placeholders so code can reference names safely
    REQUEST_COUNT = None
    REQUEST_LATENCY = None
    MODEL_INFER_INPROGRESS = None
    MODEL_INFER_DURATION = None


# -------------------------
# Models API
# -------------------------


class ModelInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    modified_ts: float


def _discover_models() -> List[ModelInfo]:
    models_dir = Path(os.getenv("MODELS_DIR", "models"))
    items: List[ModelInfo] = []
    if not models_dir.exists() or not models_dir.is_dir():
        return items
    for p in sorted(models_dir.iterdir()):
        if p.is_file():
            try:
                stat = p.stat()
                items.append(
                    ModelInfo(
                        name=p.stem,
                        path=str(p.resolve()),
                        size_bytes=stat.st_size,
                        modified_ts=stat.st_mtime,
                    )
                )
            except Exception:
                continue
    return items


@app.get("/health")
def health():
    payload = {
        "status": "ok",
        "uptime": round(uptime_seconds(), 2),
        "version": os.getenv("VERSION", "0.0.0"),
    }
    return JSONResponse(status_code=200, content=payload)


@app.get("/ready")
def ready():
    result = check_readiness()
    if result["ok"]:
        return JSONResponse(status_code=200, content={"status": "ready", **result["details"]})
    return JSONResponse(status_code=503, content={"status": "not-ready", **result["details"]})


@app.get("/")
def index():
    return {"msg": "Petra backend (health endpoints available at /health and /ready)"}


# --- Authentication protected endpoint example
from .auth import get_current_user


@app.get("/api/v1/me")
def who_am_i(user=Depends(get_current_user)):
    """Protected endpoint: returns decoded user info from the JWT token.

    Requires Authorization: Bearer <token> header. If missing or invalid, returns 401.
    """
    return {"user": user.dict()}
