import os
import time
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# Prometheus client
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from .auth import get_current_user
from .embeddings import EmbeddingEngine, chunk_text


start_time = time.time()


def uptime_seconds() -> float:
    return time.time() - start_time


app = FastAPI(title="Petra GPT Service - Backend")


def check_readiness() -> Dict[str, object]:
    mode = os.getenv("MODE", "local")
    details = {"mode": mode}
    if mode == "local":
        details["db_ok"] = None
        details["indexes_ok"] = None
        return {"ok": True, "details": details}

    db_path = Path(os.getenv("DATABASE_PATH", "data/db.sqlite"))
    index_dir = Path(os.getenv("INDEX_DIR", "data/indexes"))
    details["db_path"] = str(db_path)
    details["index_dir"] = str(index_dir)
    details["db_ok"] = db_path.exists()
    details["indexes_ok"] = index_dir.exists()
    ok = details["db_ok"] and details["indexes_ok"]
    return {"ok": ok, "details": details}


# -------------------------
# Metrics
# -------------------------
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() in ("1", "true", "yes")

if METRICS_ENABLED:
    REQUEST_COUNT = Counter("petra_http_requests_total", "Total HTTP requests", ["method", "path", "status"])
    REQUEST_LATENCY = Histogram("petra_http_request_latency_seconds", "HTTP request latency seconds", ["method", "path"])

    # embeddings metrics
    EMBEDDING_REQUESTS = Counter("embedding_requests_total", "Total embedding requests", ["type", "status"]) 
    EMBEDDING_LATENCY = Histogram("embedding_latency_seconds", "Embedding request latency seconds", ["type"]) 
    EMBEDDING_BATCH_SIZE = Histogram("embedding_batch_size_distribution", "Distribution of embedding batch sizes")
    EMBEDDING_CHUNK_COUNT = Counter("embedding_chunk_count", "Number of chunks created for chunked embeddings")


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
    REQUEST_COUNT = None
    REQUEST_LATENCY = None
    EMBEDDING_REQUESTS = None
    EMBEDDING_LATENCY = None
    EMBEDDING_BATCH_SIZE = None
    EMBEDDING_CHUNK_COUNT = None


@app.get("/metrics", tags=["observability"], summary="Prometheus metrics")
def metrics():
    if not METRICS_ENABLED:
        raise HTTPException(status_code=404, detail="metrics disabled")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# -------------------------
# Embeddings (API endpoints)
# -------------------------


class EmbeddingRequest(BaseModel):
    input: str


class BatchEmbeddingRequest(BaseModel):
    inputs: List[str]


class EmbeddingResponse(BaseModel):
    embedding: List[float]


class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]


# safe defaults
engine = EmbeddingEngine(dim=int(os.getenv("EMBED_DIM", "8")), max_input_chars=int(os.getenv("EMBED_MAX_CHARS", "20000")))


@app.post("/embeddings", response_model=EmbeddingResponse, tags=["embeddings"], summary="Create embedding for single text")
def create_embedding(req: EmbeddingRequest):
    start = time.time()
    status = "error"
    try:
        emb = engine.encode(req.input)
        status = "ok"
        return EmbeddingResponse(embedding=emb)
    finally:
        if METRICS_ENABLED:
            EMBEDDING_REQUESTS.labels(type="single", status=status).inc()
            EMBEDDING_LATENCY.labels(type="single").observe(time.time() - start)


@app.post("/embeddings/batch", response_model=BatchEmbeddingResponse, tags=["embeddings"], summary="Create embeddings for a batch of texts")
def create_embeddings_batch(req: BatchEmbeddingRequest):
    start = time.time()
    status = "error"
    try:
        batch = req.inputs
        if len(batch) == 0:
            status = "ok"
            return BatchEmbeddingResponse(embeddings=[])
        if len(batch) > 1024:
            # protection against huge batches
            raise HTTPException(status_code=400, detail="batch too large")
        embeddings = engine.encode_batch(batch)
        status = "ok"
        return BatchEmbeddingResponse(embeddings=embeddings)
    finally:
        if METRICS_ENABLED:
            EMBEDDING_REQUESTS.labels(type="batch", status=status).inc()
            EMBEDDING_BATCH_SIZE.observe(len(req.inputs))
            EMBEDDING_LATENCY.labels(type="batch").observe(time.time() - start)


@app.post("/embeddings/chunk", response_model=BatchEmbeddingResponse, tags=["embeddings"], summary="Create embeddings by chunking a long text")
def create_embeddings_chunk(req: EmbeddingRequest, chunk_size: int = 512, overlap: int = 64):
    start = time.time()
    status = "error"
    try:
        chunks = chunk_text(req.input, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            status = "ok"
            return BatchEmbeddingResponse(embeddings=[])
        if len(chunks) > 1024:
            raise HTTPException(status_code=400, detail="too many chunks")
        if METRICS_ENABLED:
            EMBEDDING_CHUNK_COUNT.inc(len(chunks)) if hasattr(EMBEDDING_CHUNK_COUNT, 'inc') else None
        embeddings = engine.encode_batch(chunks)
        status = "ok"
        return BatchEmbeddingResponse(embeddings=embeddings)
    finally:
        if METRICS_ENABLED:
            EMBEDDING_REQUESTS.labels(type="chunk", status=status).inc()
            EMBEDDING_LATENCY.labels(type="chunk").observe(time.time() - start)


# -------------------------
# Models API (existing)
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


@app.get("/api/v1/models", response_model=List[ModelInfo], tags=["models"], summary="List available models")
def list_models():
    return _discover_models()


@app.get("/api/v1/models/{name}", response_model=ModelInfo, tags=["models"], summary="Get model details")
def get_model(name: str):
    items = _discover_models()
    for m in items:
        if m.name == name:
            return m
    raise HTTPException(status_code=404, detail="model not found")


@app.get("/health")
def health():
    payload = {"status": "ok", "uptime": round(uptime_seconds(), 2), "version": os.getenv("VERSION", "0.0.0")}
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


# Authentication protected endpoint example
@app.get("/api/v1/me")
def who_am_i(user=Depends(get_current_user)):
    return {"user": user.dict()}
import os
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, Response
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Depends

from .embeddings import EmbeddingEngine, chunk_text

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
    # Embeddings-specific metrics
    EMBEDDING_REQUESTS = Counter("embedding_requests_total", "Total embedding requests", ["type","status"]) 
    EMBEDDING_LATENCY = Histogram("embedding_latency_seconds", "Embedding request latency seconds", ["type"]) 
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

        class EmbeddingRequest(BaseModel):
            input: str

        class BatchEmbeddingRequest(BaseModel):
            inputs: List[str]

        class EmbeddingResponse(BaseModel):
            embedding: List[float]

        class BatchEmbeddingResponse(BaseModel):
            embeddings: List[List[float]]

        engine = EmbeddingEngine(dim=int(os.getenv("EMBED_DIM", "8")), max_input_chars=int(os.getenv("EMBED_MAX_CHARS", "20000")))




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
