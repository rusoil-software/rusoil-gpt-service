import os
import time
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

# prometheus
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

start_time = time.time()
app = FastAPI(title="Petra GPT Service - Backend")

# basic prometheus metrics
HEALTH_CHECKS = Counter('petra_health_checks_total', 'Number of health checks')
READY_CHECKS = Counter('petra_ready_checks_total', 'Number of readiness checks')


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
    model_dir = Path(os.getenv('MODEL_DIR', 'models'))
    if not model_dir.exists() or not model_dir.is_dir():
        return []

    result = []
    for p in sorted(model_dir.iterdir()):
        if p.is_file():
            stat = p.stat()
            result.append({
                'name': p.name,
                'size': stat.st_size,
                'modified': stat.st_mtime,
            })
    return result


@app.get("/api/v1/models/{name}")
def get_model(name: str) -> Dict[str, object]:
    model_dir = Path(os.getenv('MODEL_DIR', 'models'))
    p = model_dir / name
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail='model not found')
    stat = p.stat()
    return {'name': p.name, 'size': stat.st_size, 'modified': stat.st_mtime}


@app.get("/")
def index():
    return {"msg": "Petra backend (health endpoints available at /health and /ready)"}
