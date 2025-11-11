import os
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
