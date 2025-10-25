## petra-gpt-service — Technical Vision (living blueprint)

This document records a concise, KISS-minded technical blueprint for petra-gpt-service. We'll iterate section-by-section; this file will grow as we confirm each part.

Section: Technologies (MVP, KISS)
---------------------------------

Goal: pick the smallest, lowest-friction stack that lets a student run the system locally (laptop/home server) and lets us evolve to a production deployment later.

Primary decisions (agreed):
- Local-first model strategy: use local quantized models for text and embeddings (llama.cpp / ggml-backed models via `llama-cpp-python` or similar) for testing to avoid API costs.
- Frontend: React (Vite + React) for the MVP UI (simple single-page chat app). Reason: developer productivity and easy extension to VSCode/web integrations.
- Vector store: `faiss-cpu` for local vector indexing and nearest-neighbor retrieval (fast, widely used). We'll provide a tiny fallback to brute-force numpy if faiss installation fails.
- Metadata DB: SQLite for MVP (single-file, zero-ops). Postgres reserved for production.
- Redis: deferred to later; keep it optional and out of the critical path for MVP.
- Auth/SSO: deferred for MVP — local mode will run without SSO. Production will integrate OIDC/SSO.

Minimal stack summary (MVP):
- Backend: FastAPI + Uvicorn (async, minimal). One service that handles REST + WebSocket streaming.
- Frontend: React app (Vite) that connects to backend via WebSocket for streaming chat responses.
- Local model inference: `llama-cpp-python` (or direct llama.cpp subprocess) using quantized GGML model files stored in `models/`.
- Embeddings: local sentence-transformers (small model) or light-weight embedding from llama model if preferred.
- Vector index: `faiss-cpu` storing indexes on disk; vector metadata in SQLite.
- Storage: local filesystem for uploads (`data/uploads/`), `models/` for model artifacts.
- Packaging: single Dockerfile that builds the backend and serves the frontend assets; separate dev-mode docker-compose recipe that mounts model files and local DB.
- Dependency / env: Python 3.11+, use Poetry (recommended) or pip + requirements.txt; Node 18+ for frontend.

Why these choices (short):
- Local quantized models keep costs zero for initial testing and let students run the system entirely offline.
- React offers a small amount of upfront complexity but pays off for maintainability, testing, and later VSCode/web integration.
- Faiss + SQLite is simple and performs well for campus-scale datasets in early stages.
- Avoid Redis/Postgres/S3 in MVP to keep the setup friction minimal.

Implementation notes (practical, KISS)
- Provide a `MODE` flag: `MODE=local` (default) or `MODE=prod`. `local` forces using local models, SQLite, local FS; `prod` will enable adapters for remote embeddings, Postgres, S3, and Redis.
- Model layout: `models/<model-name>/model.ggml` and optional tokenizer/config. Document how to place/download a quantized model in README.
- Embeddings config: by default use a small local sentence-transformers model stored in `models/embeddings/`.
- Vector index path: `data/indexes/<collection>.faiss` and SQLite metadata `data/db.sqlite`.
- Simple CLI commands (README):
  - `poetry install` (backend)
  - `npm install` and `npm run dev` (frontend)
  - `docker build -t petra-gpt-service .` and `docker run -p 8000:8000 -v ./models:/app/models -v ./data:/app/data petra-gpt-service`

Developer ergonomics
- Local dev: provide a `docker-compose.dev.yml` that mounts `models/` and `data/` so students can run with a single command.
- Tests: small unit tests for API + integration test that exercises a full chat round-trip with a tiny quantized test model.

Section: Development (dev workflow, CI, testing, local dev experience)
-----------------------------------------------------------------

Goal: make it trivial for contributors and students to run, test, and iterate on the project locally while keeping CI and quality checks minimal and useful.

Key choices (agreed):
- Python dependency management: Poetry (recommended).
- Frontend: Vite + React + TypeScript.

Dev environment (local-first, KISS):
- Monorepo layout (recommended): `backend/` (FastAPI) and `frontend/` (Vite React TS) in the same repository for simple coordination and single Docker build flow.
- `docker-compose.dev.yml` to orchestrate backend, frontend dev server, and an optional tiny service for models if needed. Mount `models/` and `data/` for easy iteration.
- `.env` file for local environment variables; keep sensible defaults in `.env.example`.

Quality & automation (minimal CI):
- Use GitHub Actions with two small workflows:
  - `lint-and-test.yml`: run Python linters (ruff) and tests (pytest) for backend, and `eslint + tsc --noEmit` for frontend. Run on PRs.
  - `build-and-smoke.yml`: build Docker image and run a smoke test (start container, hit health endpoint) for main branch deploys.
- Pre-commit hooks: ruff (format & lint), isort, and simple git hooks to run lightweight checks locally.

Testing strategy (KISS):
- Unit tests: use `pytest` in backend; keep tests small and fast.
- Integration test: one minimal E2E test that launches the backend in test mode (uses a tiny quantized test model or a mocked model interface) and exercises a chat roundtrip.
- Frontend tests: minimal smoke test that ensures the build succeeds; more extensive UI tests can come later.

Model testing note:
- For tests and CI, provide a mocked model adapter so CI does not require GPU/large model downloads. Local developers can opt into a small test model stored in `tests/fixtures/models/`.

Developer commands (local, PowerShell-friendly examples)
```powershell
# Backend
poetry install
poetry run pytest

# Frontend
cd frontend
npm install
npm run dev

# Development compose (mounts models/ and data/)
docker compose -f docker-compose.dev.yml up --build
```

IDE and DX
- Recommend VSCode with the Python and ESLint/TS plugins. Add a `.vscode/launch.json` for quick backend attach and frontend dev launch configurations.

Section: Project structure (monorepo, KISS)
-----------------------------------------

Goal: an obvious, minimal repository layout that a student can clone and start with one or two commands. Keep source files grouped, keep configuration minimal, and avoid cross-language complexity.

Top-level layout (recommended):

```
petra-gpt-service/
├─ backend/                # FastAPI backend source (python package)
│  ├─ app/
│  │  ├─ main.py           # ASGI entrypoint
│  │  ├─ api/              # REST + websocket handlers
│  │  ├─ core/             # config, logging, utils
│  │  ├─ services/         # orchestration, agent runner
│  │  └─ adapters/         # model adapters, storage adapters
│  ├─ tests/               # backend tests
├─ frontend/               # Vite + React + TypeScript app
│  ├─ src/
│  ├─ public/
│  └─ tests/
├─ models/                 # local quantized model files (gitignored)
├─ data/                   # runtime data: uploads, indexes, sqlite DB
│  ├─ uploads/
│  ├─ indexes/
│  └─ db.sqlite
├─ infra/                  # optional: k8s/helm manifests or helper scripts
├─ docs/                   # living docs (idea.md, vision.md, etc.)
├─ .github/workflows/      # CI workflows
├─ docker-compose.dev.yml  # developer compose that mounts models/data
├─ Dockerfile              # single image for simple deployments
├─ pyproject.toml          # Poetry / backend deps (root-managed)
├─ package.json            # frontend tooling (inside frontend/ too)
├─ README.md
└─ .env.example
```

Notes and conventions
- Use a single top-level `pyproject.toml` managed by Poetry for backend dependencies. Keep frontend dependencies in `frontend/package.json` (Vite default).
- Keep `models/` and `data/` directories out of version control; add sensible `.gitignore` entries and document how to obtain quantized models in `docs/README-models.md`.
- Keep infra optional: `infra/` can hold Kubernetes manifests or Helm charts later; not required for MVP.
- Tests live next to code: `backend/tests/` and `frontend/tests/` with a light CI job.
- Keep DB migrations out of the critical path for MVP; for production use, add `alembic` and a migrations plan when switching to Postgres.

Developer shortcuts and scripts
- `Makefile` or `tools/` scripts for common tasks (build, test, format). Example targets:
  - `make dev` -> run `docker compose -f docker-compose.dev.yml up --build`
  - `make test` -> run backend + frontend quick checks
- Place small helper scripts in `tools/` (e.g., `tools/download_test_model.py`) to simplify getting test models.

Example developer flow (KISS)
1. Clone repo and create `.env` from `.env.example`.
2. Place quantized model in `models/<model-name>/` or run `tools/download_test_model.py`.
3. `poetry install` (root) and `cd frontend && npm install`.
4. `docker compose -f docker-compose.dev.yml up --build` or `make dev`.

Next: I'll draft the `project architecture` section (component responsibilities, runtime interactions, and data flows). No extra questions for this step unless you want to add any required integration points now.

Section: Project architecture (components, runtime interactions, data flows)
---------------------------------------------------------------------

Goal: describe the minimal runtime components and how they interact for the MVP, with an emphasis on simple contracts and clear upgrade paths.

ASCII overview (KISS)

```
Client (Browser / VSCode)  <--websocket/HTTP-->  FastAPI Backend  <--adapter-->  Local Model (llama.cpp)
                                         |                               
                                         |---> Faiss index (disk) + SQLite metadata
                                         |---> Local filesystem (uploads)
                                         `---> Optional: Redis / Postgres (prod)
```

Components and responsibilities
- Client (frontend): React SPA that opens a WebSocket for streaming chat; handles uploads and displays responses.
- FastAPI Backend: single orchestrator service exposing REST and WebSocket endpoints; validates requests, manages sessions, coordinates RAG and agent flows, and sends/receives from model adapters.
- Model Adapter: small pluggable layer that hides llama.cpp or any other model-serving backend behind a simple API (generate(prompt, params) -> stream/chunked responses; embed(text) -> vector).
- Vector Store: Faiss index on disk; metadata in SQLite linking vectors to documents and source files.
- Storage: local filesystem for models, uploads, and index files. In prod, swap to S3-compatible buckets and Postgres.
- Optional infra (prod): Redis for rate-limiting/pubsub, Postgres for metadata, object storage for large files.
- Observability: structured logs to stdout, `/metrics` endpoint for Prometheus, and health/readiness endpoints.

Typical request flow (chat roundtrip, simplified)
1. Client opens WebSocket and sends a chat message (prompt, context id, mode).
2. Backend validates auth/context (local mode: minimal checks) and looks up relevant documents via vector retriever (Faiss + SQLite metadata).
3. Backend constructs a combined prompt (system + retrieved context + user message) and calls Model Adapter.generate().
4. Model Adapter runs inference with local llama.cpp and streams tokens back to Backend.
5. Backend forwards tokens to the client via WebSocket; simultaneously logs metadata about the request and stores conversation entries in SQLite.

Agent / vibe-coding flow (simple)
- For multi-step agent workflows, the Backend coordinates small steps via the Model Adapter and local sandboxed runners for actions like `run-tests` or `apply-patch`.
- Keep agent actions deterministic and permissioned; sandbox execution must be off by default and gated for local developer use only.

Contracts and interfaces (tiny)
- Model Adapter API (internal):
  - generate(prompt: str, params: dict) -> Async iterator[str] (streamed tokens)
  - embed(text: str) -> List[float]
- Retriever API: search(query_vector: List[float], top_k: int) -> List[DocumentMetadata]

Scaling & upgrade notes (practical, KISS)
- Local: single process runs Backend + Model Adapter on one machine; Faiss index and SQLite on disk.
- When moving to multi-node/prod:
  - Separate model-serving into dedicated nodes (Triton/Ray/torchserve) or multiple containers each running llama.cpp for mid-sized GPU fleets.
  - Migrate SQLite -> Postgres and store Faiss indexes on shared filesystems or use managed vector stores.
  - Introduce Redis for pub/sub and rate-limiting; add an API Gateway or ingress controller.
- Keep backward-compatible adapter contracts so the Backend does not need deep changes when swapping model-serving backends.

Security & isolation (baseline)
- Local mode: minimal auth; warn users that data is local and unencrypted by default.
- Prod: require OIDC/SSO, encrypt storage at rest, isolate model execution from the web-facing process (separate containers), and sandbox agent actions.

Section: Data model (entities and minimal SQLite schema)
-----------------------------------------------------

Goal: provide a tiny, practical schema that supports local-mode use (SQLite) and can be migrated to Postgres later. Keep schemas small and indexed for the common flows: chat sessions, document storage, RAG vector metadata, and uploads.

Primary entities (KISS):
- users: optional for local mode; identifies a developer or student (string id or local username).
- conversations: a logical chat session (conversation_id) that groups messages.
- messages: individual chat messages (role, text, timestamp). Stored for simple history and auditing.
- documents: uploaded or ingested documents (filename, text, source, created_at).
- vectors: metadata table linking Faiss vectors to documents (document_id, vector_id, embedding_dim, created_at, chunk_index, score cached if needed).
- models: record of model artifacts in `models/` (name, path, quantization info).
- uploads: file metadata for user uploads (path, content_type, size).

Minimal SQLite schema (example)

```sql
-- users (optional for MVP local mode)
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  display_name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- conversations
CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  title TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- messages
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL, -- user | assistant | system
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

-- documents (ingested files / uploaded text chunks)
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  title TEXT,
  source TEXT, -- original filename or URL
  content TEXT,
  content_type TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- vectors (Faiss index pointers and metadata)
CREATE TABLE IF NOT EXISTS vectors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id TEXT,
  chunk_index INTEGER DEFAULT 0,
  vector_id INTEGER, -- pointer/index in Faiss
  embedding_dim INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);

-- models
CREATE TABLE IF NOT EXISTS models (
  name TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  format TEXT,
  quantized BOOLEAN DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- uploads
CREATE TABLE IF NOT EXISTS uploads (
  id TEXT PRIMARY KEY,
  filename TEXT,
  path TEXT,
  content_type TEXT,
  size INTEGER,
  uploaded_by TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Storage notes (how vectors are stored)
- Faiss stores dense vectors in its own on-disk index files under `data/indexes/`.
- The `vectors` table above links document chunks to Faiss vector ids. On retrieval, the retriever will:
  1. compute query embedding via the model adapter,
  2. query Faiss for nearest neighbors (returns vector ids + distances),
  3. lookup `vectors` (and `documents`) in SQLite to fetch source text and metadata.

Indexes and performance (SQLite tips)
- Add indexes on `messages.conversation_id`, `vectors.document_id`, and `documents.created_at` for common queries.
- Keep `content` column in `documents` for small-to-medium docs; for large files, store in `uploads/` and keep a short excerpt in `documents.content`.

Migration note (Postgres)
- When moving to Postgres, types remain mostly identical. Replace `AUTOINCREMENT` with `SERIAL` or `GENERATED` and add proper constraints/indices. Use Alembic for migrations when you switch to Postgres.

Section: User interactions (prioritized flows, UI contracts, KISS UX)
----------------------------------------------------------------

Goal: design minimal, discoverable interactions so students can get value immediately. Prioritize a simple chat + document Q&A flow for MVP, while keeping hooks for future agent-based vibe-coding and VSCode integrations.

Priority: Simple chat + document Q&A (MVP)
- Why: lowest friction for students — upload course notes or lecture PDFs and ask questions. This exercises embeddings, vector retrieval, and the chat UI without heavy sandboxing or code-execution risks.

Client flows (chat + doc Q&A)
- Open chat UI (React SPA). The default view: recent conversations list + composer input.
- Upload flow: user clicks "Upload document", picks a file (PDF or .txt). Client uploads to backend (`/upload`) which stores file in `data/uploads/`, extracts text (simple extractor), chunks, computes embeddings, and inserts vectors into Faiss and metadata into SQLite.
- Ask flow:
  1. User types a question and presses send.
  2. Frontend sends message over WebSocket: { conversation_id, message, mode: "qa" }.
  3. Backend computes query embedding, performs Faiss search (top_k, default 5), fetches corresponding document chunks from SQLite, constructs a prompt (system + retrieved chunks + user question), and calls Model Adapter.generate().
  4. Backend streams tokens back to client over WebSocket. Client displays tokens progressively.
  5. After completion, backend stores message & assistant response in `messages` and optionally stores a short provenance record linking response to retrieved documents.

UX details (KISS):
- Show retrieved document snippets (collapsed) under the assistant's response with a "show source" button.
- Allow user to "regenerate" response or increase `top_k`/model temperature via small UI controls.
- Conversations are local by default; provide an export button to save conversation JSON.

Secondary: Vibe-coding / Agent workflows (lightweight)
- Keep this out of the critical path for MVP. Design a clearly gated agent mode that can be enabled per-user.
- Minimal agent example: "Suggest fix for failing test"
  - User provides repo snippet or links to small code file (upload or paste).
  - Backend creates a temporary sandbox (local script runner) and a short orchestrator that runs steps: generate patch -> apply to temp copy -> run tiny test runner -> collect results -> iterate a small fixed number of times.
- Security: sandboxing is disabled in default local dev mode, and in any shared environment agent actions must be explicitly allowed and run in isolated containers.

VSCode integration (minimal hooks)
- Basic extension features (phase 1): selection -> command palette -> send selection to Petra chat -> display response in a panel.
- UX: user selects code, presses `Ctrl+Shift+P -> Petra: Ask`, extension opens a small input, the query is sent to local backend (configured via `petra-gpt.host` in extension settings), the reply is shown in a WebView panel. For now, no automatic code-patching; only suggestion copy-paste.

Accessibility and small-device UX
- Ensure chat UI works on narrow screens; use readable fonts and clear contrast. Keep controls minimal: upload, send, regenerate, settings.

API contract (minimal)
- WebSocket messages:
  - Client -> Server: { type: 'message', conversation_id, user_id?, content, mode? }
  - Server -> Client: streamed tokens events { type: 'token', conversation_id, token } and terminal events { type: 'response_end', conversation_id, metadata }
- Upload API (HTTP): `POST /upload` multipart/form-data -> returns document_id and a short text excerpt.

Telemetry & privacy (local-first)
- Local mode: do not send telemetry by default. Add an opt-in to enable anonymous usage metrics for helping prioritize features.
- When saving provenance links (which document chunks contributed), avoid storing full user files in any remote telemetry.

Section: Data storage — bucket and databases (local + Yandex S3 + Postgres)
-----------------------------------------------------------------------

Local defaults (KISS)
- Models: stored under `models/<model-name>/` (gitignored). Small test models can be added to `tests/fixtures/models/` for CI.
- Uploads: stored under `data/uploads/` with a stable path scheme: `data/uploads/<upload-id>/<filename>`.
- Faiss indexes: stored under `data/indexes/<collection>.faiss` and other Faiss support files.
- SQLite DB: `data/db.sqlite` for metadata (documents, vectors, conversations, models).

Production / cloud adapters (Yandex S3 and Postgres)
- Object storage (Yandex S3): store large files (uploads, model artifacts, large media) in an S3 bucket.
  - Environment variables:
    - S3_ENDPOINT (e.g., https://storage.yandexcloud.net)
    - S3_REGION
    - S3_ACCESS_KEY
    - S3_SECRET_KEY
    - S3_BUCKET
  - Use an S3 client (boto3 or minio-py) with an adapter in `backend/app/adapters/storage.py` so code uses a simple `put_object(key, fileobj)` / `get_object(key)` API.
  - For local dev, provide `docker-compose` with MinIO and pre-configured buckets to emulate Yandex S3.

- Relational DB (Postgres): store metadata (documents, vectors table, conversations, messages, users) in Postgres in prod.
  - Environment variable: `DATABASE_URL` (postgres://user:pass@host:5432/dbname)
  - Use SQLAlchemy with a small `db` layer and Alembic for migrations when moving beyond MVP.

Design mapping (what goes where)
- Objects (S3/MinIO/local FS):
  - Uploaded files (PDFs, images, code archives)
  - Model artifacts (optionally)
  - Large media
- Relational metadata (SQLite/Postgres):
  - documents, vectors metadata, messages, conversations, provenance links, model records
- Faiss index files: stored as objects on shared filesystem or S3-backed filesystem in prod. For high-scale, consider a managed vector store, but keep Faiss local for MVP.

Access control & security (storage)
- Always require credentials for S3 access; read credentials from environment variables or secret stores in cloud.
- Encrypt objects at rest in production (use provider features) and enable TLS for S3 endpoints.
- For local mode, document that files are stored unencrypted on disk.

Backups & retention (KISS)
- SQLite local backup: periodic copy of `data/db.sqlite` and `data/indexes/` to `backups/` with timestamps. Provide `tools/backup_local.py` to do this simply.
- Production: configure automated backups for Postgres and enable versioned buckets for S3 so objects can be restored.
- Retention policy: keep uploads for X days by default (configurable). Provide a simple garbage-collection script that removes unreferenced uploads.

Migration path (local → prod)
1. Run with local FS + SQLite; ensure data model and vector metadata are stable.
2. Provision Postgres; run a one-time migration that copies SQLite tables into Postgres via ETL or use a script to read and insert rows.
3. Provision S3 (Yandex) and copy large files (uploads and model artifacts) from disk into buckets. Update metadata paths to S3 keys.
4. Switch `MODE=prod` and verify correctness in a staging environment.

Configuration variables (suggested)
- `MODE=local|prod`
- `DATABASE_URL` (Postgres)
- `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
- `FAISS_INDEX_DIR` (path)
- `UPLOADS_DIR` (local path)

Operational notes (minimal)
- Start with MinIO for on-prem testing: it's lightweight and matches S3 semantics.
- Keep Faiss indexes on a single node for MVP; moving to a shared/managed vector store is a phase-2 decision.
- When moving to cloud, ensure the Postgres instance and S3 bucket are in the same region to reduce egress costs.

Section: RAG (Retrieval-Augmented Generation) — minimal pipeline
----------------------------------------------------------------

Goal: provide a minimal, reliable retrieval pipeline that works locally with Faiss and local embeddings, and can be swapped for managed vector stores later. Keep the implementation explicit (no heavy frameworks) so students can understand and modify each step.

Core components (KISS):
- Chunker: split documents into chunks (configurable chunk_size, chunk_overlap). Default: chunk_size=2000 chars (~500 tokens), overlap=256 chars.
- Embedder: local embedding model (sentence-transformers small model) or llama-cpp embedding when available.
- Indexer: Faiss (faiss-cpu) storing vectors on disk (`data/indexes/`). Keep a thin metadata layer in SQLite mapping vector ids to document chunks.
- Retriever: given a query, compute embedding, query Faiss (top_k), and return ordered document chunks with distances.
- Reranker (optional): lightweight re-ranking using the LLM for higher precision.

Minimal RAG pipeline (request time)
1. User sends question.
2. Backend computes query embedding via Embedder.
3. Retriever queries Faiss for top_k neighbors (configurable, default 5–10).
4. Backend fetches corresponding chunks from SQLite and optionally runs a quick reranking step.
5. Backend assembles a prompt consisting of:
  - system instructions (safety / persona / output format)
  - short retrieved snippets labeled with source metadata
  - user question
6. Call Model Adapter.generate() with the assembled prompt and stream back results.

Indexing pipeline (ingest time)
1. Extract text from uploaded documents (PDF/txt) via a simple extractor.
2. Normalize text (strip whitespace, remove boilerplate), split into chunks, compute embeddings for each chunk.
3. Insert embeddings into Faiss index and record metadata rows in SQLite linking `vector_id` to `document_id` and `chunk_index`.
4. Persist Faiss index to disk (`data/indexes/<collection>.faiss`).

Configuration knobs (tune as needed)
- chunk_size, chunk_overlap
- embedding model path
- top_k for retrieval
- rerank threshold (when to run LLM reranker)
- similarity metric (cosine vs inner product) — store normalized vectors if using cosine.

Caching & performance
- Cache recent query embeddings and retrieval results in a small in-memory LRU cache to avoid repeated nearest-neighbor lookups for identical queries.
- Batch embeddings during ingest to leverage CPU/GPU efficiency.

Maintenance & reindexing
- Provide `tools/reindex.py` that scans `data/uploads/` or `documents` table and rebuilds Faiss indexes from SQLite metadata.
- When changing embedding model, reindex all documents (document the process and provide scripts to make it simple).

Provenance & explainability
- Store provenance metadata linking responses to the top contributing chunks (document_id, chunk_index, score). Present these as "sources" in the UI so students can verify answers.

Why avoid heavy frameworks initially
- Keeping an explicit, small RAG implementation (chunker + embedder + faiss + sqlite) makes the behavior transparent and easy to debug for students. If desired, we can introduce LangChain-style helpers later behind adapter layers.

Section: VSCode extension (minimal design)
----------------------------------------

Goal: provide a tiny, local-first VSCode extension that lets students select code/text and ask the Petra assistant for help without leaving the editor. Keep behavior read-only (suggestions only) for safety.

Core features (KISS):
- Command: `Petra: Ask Selection` — send the selected text (or current file) to the local Petra backend and show the assistant's reply in a WebView panel.
- Command: `Petra: Open Chat` — open a lightweight chat panel inside VSCode that mirrors the browser UI for the current workspace.
- Settings: `petra-gpt.host` (default `http://localhost:8000`), `petra-gpt.timeout`, and `petra-gpt.mode` (local|prod).

Message flow (simple)
1. User selects text and runs `Petra: Ask Selection`.
2. Extension packages a payload { selection, filePath?, workspaceFolder? } and POSTs to `petra-gpt.host/api/v1/vscode/ask` (or sends via WebSocket if available).
3. Backend returns a streamed or complete response. The extension renders response tokens progressively in the WebView and provides buttons: Copy, Insert (paste into file at cursor), Open in Chat.

Security & UX choices
- The extension targets local-first workflows and uses user-configured `petra-gpt.host`. It must warn if connecting to an untrusted remote host.
- No automatic file edits by default. If a user wants to apply a suggested patch, they must explicitly click `Insert` which pastes the suggestion at the cursor; an optional confirm dialog can be enabled in settings.
- Authentication: extension can support token-based auth by reading `petra-gpt.token` setting; for MVP, keep auth optional and document how to set tokens for prod.

Packaging and testing (KISS)
- Keep extension in `extensions/vscode-petra-gpt/` inside the monorepo. Use `yo code` minimal TypeScript extension scaffold.
- Provide a simple `npm run dev` that launches the extension in Extension Development Host and points it to the local backend.
- Unit tests: small integration test that mocks the backend (or uses a local test server) and asserts the extension displays responses.

Developer notes
- The extension should reuse the same WebSocket/HTTP message contract used by the frontend to keep server code simple.
- Keep WebView UI minimal — reuse some frontend React components compiled separately or implement a tiny HTML UI inside the extension.

Section: Work scenarios (short, actionable workflows)
---------------------------------------------------

Goal: describe concrete, minimal workflows for common users so we can validate the system with real tasks and tests. Each scenario lists the intent, steps, required components, and acceptance criteria for an MVP run.

1) Student — Local coding & Q&A (primary)
- Intent: student runs Petra locally on their laptop to get help with class notes and small code snippets.
- Steps:
  1. Clone repo, place a quantized model in `models/` or run `tools/download_test_model.py`.
  2. `poetry install` and `cd frontend && npm install`.
  3. `docker compose -f docker-compose.dev.yml up --build`.
  4. Open browser at `http://localhost:8000`, upload course notes or paste code, ask questions in chat.
- Required components: local llama.cpp model, FastAPI backend, React frontend, Faiss index (created on first ingest), SQLite DB.
- Acceptance criteria: user can upload a PDF or paste code, ask a question, and receive a streamed answer with at least one source snippet shown.

2) Instructor — Multi-user classroom instance (small cluster)
- Intent: a professor runs Petra on a small server to allow several students to use the service concurrently for a course.
- Steps:
  1. Provision a small VM (2–4 CPU, 8–16 GB RAM) or single-node cluster.
  2. Deploy via Docker Compose for initial testing (`docker compose up -d`) with MODE=prod but using local Postgres/MinIO or managed services.
  3. Configure storage (MinIO or Yandex S3) and Postgres; preload course materials and build Faiss indexes.
  4. Provide students the URL and simple usage instructions.
- Required components: Backend containers, optional MinIO, Postgres, Faiss indexes stored on disk or shared mount.
- Acceptance criteria: 10–50 concurrent users can open sessions and perform simple Q&A with acceptable latency (<5s for retrieval + model token streaming for small models).

3) Instructor — Batch grading / feedback automation
- Intent: instructor runs batch workflows to grade or provide feedback on student submissions using RAG and agent workflows.
- Steps:
  1. Upload a ZIP of student submissions or point to an uploads directory.
  2. Run ingestion script to extract text/code, chunk, embed and index.
  3. Run a batch job that iterates submissions and uses templates/prompts to generate feedback; store results in `data/outputs/` or in Postgres.
  4. Review feedback, export CSV of grades/notes.
- Required components: ingestion tooling (`tools/ingest_batch.py`), Faiss index, model adapter, small worker process or cron job.
- Acceptance criteria: for a batch of N submissions, the system produces feedback artifacts (one file per submission) and an exportable summary within a reasonable time (depends on local resources); instructor can review and accept/reject suggestions.

4) Research — data processing & experiments pipeline
- Intent: researchers use Petra to run experiments on large corpora (document ingestion, retrieval tuning, model evaluation).
- Steps:
  1. Provision a workstation or cluster with larger storage and CPU/GPU resources.
  2. Use `tools/ingest_corpus.py` to ingest large datasets into Faiss and SQLite/Postgres.
  3. Run evaluation scripts that send curated queries and measure retrieval+answer quality. Iterate embedding or chunking choices.
  4. Store experiment metadata and results in a simple experiments table (or external ML tracking tool).
- Required components: scalable storage (S3 or large local disk), batch ingestion tooling, experiment runner, optional GPU nodes for heavy models.
- Acceptance criteria: researcher can run reproducible experiments, collect metrics, and reindex with different embeddings or chunking settings.

Cross-cutting notes (KISS)
- Start small: validate student local flow first; it's the fastest feedback loop.
- Provide simple scripts under `tools/` to automate common tasks (download models, ingest, reindex, batch-run feedback).
- For any scenario that requires higher concurrency or long-running jobs, prefer separating worker processes from the web-facing API and use simple job queues (disk-based or Redis when added).

Section: Deploy (Docker, docker-compose, minimal Kubernetes) — KISS
----------------------------------------------------------------

Goal: give a tiny, reproducible deployment path that students and instructors can run, and a clear, minimal upgrade path to production.

Local / developer deploy (recommended first step)
- Provide `docker-compose.dev.yml` that builds the backend image, runs the frontend dev server (or serves built static files), and optionally starts MinIO and Postgres for a near-prod experience.
- Default compose should mount `./models` and `./data` so users can plug in quantized models and persist the SQLite DB and Faiss indexes.
- Example (conceptual):
  - Backend service: builds from repo, exposes 8000, mounts code for live-reload in dev.
  - Frontend service: runs Vite in dev or serves built `dist/` in prod-like mode.
  - MinIO (optional): for simulating S3 in local dev.
  - Postgres (optional): for testing migrations; use a small local volume in dev.

Dockerfile and image layout (KISS)
- Use a multi-stage Dockerfile: build frontend assets in the first stage, install Python deps and copy backend + built frontend into a compact runtime image in the final stage.
- Keep the image able to run in either `MODE=local` or `MODE=prod` (via env var) but default to `MODE=local` for safety.
- Example runtime expectations:
  - Expose health endpoint `/health` and metrics `/metrics`.
  - Entrypoint runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Secrets, config, and migrations
- Use environment variables for secrets (DATABASE_URL, S3_*, SECRET_KEY). For local dev, `.env` and `.env.example` are fine. For any shared instance, use a secret manager.
- Include an image/recipe for running migrations (`alembic upgrade head`) as a separate init container or as a manual step in deploy docs.

Health checks and readiness
- Implement `/health` (simple liveness) and `/ready` (checks DB connectivity, optional S3 availability, and optionally a quick model-adapter probe) so orchestrators can wait for readiness.

CI & minimal rollout
- CI should build the Docker image and run a smoke test that hits `/health` and exercises one tiny API endpoint (mocked model adapter in CI).
- For simple deploys, pushing the image and running `docker compose -f docker-compose.prod.yml up -d` is sufficient.

Production (minimal, recommended steps)
- Use a container runtime (single-node VM or a small k8s cluster) and provision Postgres and object storage (S3/MinIO/Yandex). Keep Faiss indexes on a node-local disk or on a shared filesystem for small clusters.
- For Kubernetes, provide minimal manifests or Helm chart that:
  - Deploys a Deployment for the backend with replicas=1 or 2 depending on expected traffic.
  - Provides a ConfigMap/Secret for env vars.
  - Optionally deploys a small MinIO or configures the S3 adapter to a managed bucket.
  - Adds a simple HorizontalPodAutoscaler (HPA) for the backend (CPU-based or custom metrics later).

Observability and ops
- Expose Prometheus metrics and wire a basic Grafana dashboard (request rate, latency, model latency, queue length, Faiss search time). Start small: 5–10 default metrics to track.
- Log in structured JSON to stdout so logs can be collected by the platform (or left on disk in local dev).

Section: Scaling (practical staged plan)
------------------------------------------------

Goal: a pragmatic, staged approach from local laptops to a small cluster and then to model-serving at scale, keeping the same simple contracts and adapter layers.

Stage 0 — Local (student laptop)
- Run backend + model adapter on same machine. Faiss index and SQLite on local disk. Keep concurrency low and limits strict (single or few worker threads).

Stage 1 — Single-server / small VM (instructor)
- Run services via Docker Compose or a single-node k8s. Replace SQLite with Postgres, and optionally use MinIO for object storage.
- Keep model adapters colocated with the backend or in sibling containers on the same host (for small CPUs/GPU setups).

Stage 2 — Small cluster (multi-node)
- Split responsibilities: web/API tier (stateless backend), model-serving tier (stateful container per model or a model-serving system), and persistent services (Postgres, S3).
- Faiss strategy: keep per-node indexes for local datasets, or shard collections across nodes. For early stages, keep single-index-per-collection on a single node and accept limitations.


Stage 3 — Model-serving scale
- Separate model-serving: run dedicated model-serving containers or a lightweight orchestration like Ray Serve / TorchServe / Triton or multiple llama.cpp workers behind a load balancer.
- Make model adapter calls over HTTP/GRPC to dedicated workers — keep adapter contract identical so the backend code doesn't change when swapping local llama.cpp for a remote server.
- Use GPU nodes or high-CPU nodes depending on model and quantization.

Index scaling & retrieval
- For larger corpora, consider:
  - Sharding Faiss indexes by collection or time window to keep per-shard latency low.
  - Using an index-per-shard + an aggregator that queries shards in parallel and merges results (watch out for increased memory usage during merges).
  - Storing precomputed compressed vectors (float16) and normalizing vectors at ingest to optimize cosine searches.
  - For very large scale, evaluate managed vector DBs (e.g., Pinecone, Milvus, or a hosted Faiss service) or specialized services that provide horizontal scaling.

Autoscaling & scheduling hints
- Autoscale model-serving pods by queue length, request latency, or a custom Prometheus metric that tracks pending tokens to generate. This is more robust than CPU alone for model workers.
- For the stateless backend, CPU-based HPA is fine initially; for model workers use an adaptive scaler that considers GPU utilization (nvidia-dcgm-exporter metrics) or custom metrics exposed by the model-serving layer.
- Consider running model workers with pod anti-affinity and node selectors/taints for GPU nodes to avoid noisy-neighbor issues.

Resilience, safety, and cost controls
- Keep model execution isolated from the HTTP request thread; the backend should stream responses from model workers and abort/timeout requests cleanly.
- Enforce per-request quotas and token limits (configurable via env) to bound cost and protect availability.
- Implement rate-limiting and API key quotas at an ingress or gateway layer for shared instances.
- Provide a mechanism to pause or demote expensive models (e.g., heavy non-quantized models) in low-resource situations.

Key metrics and SLOs (suggested)
- Latency: p50/p95 end-to-end request latency (goal: p95 < 10s for small local models; adjust for larger models).
- Retrieval latency: Faiss search time p95 (goal: < 200ms for small indexes; depends on index size).
- Embedding time: average time to compute embeddings per query.
- Model throughput: tokens/sec and p95 token latency for model worker.
- Error rates: 5xx, timeouts, and queue saturations.
- Resource utilization: CPU, memory, GPU utilization per model worker.

Resource sizing (practical starting points)
- Student laptop (local): 2–4 vCPU, 8–16 GB RAM — use small quantized models (7B-13B quantized) and faiss-cpu.
- Instructor single-server: 4–8 vCPU, 16–64 GB RAM depending on model size; consider adding a modest GPU if using unquantized or large models.
- Small cluster (multi-node): begin with 2–4 worker nodes (8–16 vCPU each) and a single Postgres instance; size model-serving nodes separately based on throughput testing.

Index maintenance & reindexing
- Provide `tools/reindex.py` and `tools/reindex_incremental.py` for full and incremental reindexes.
- Use versioned index files (e.g., `collection.v1.faiss`) and atomically swap indexes on disk to avoid serving incomplete indexes.
- For schema or embedding-model changes, do a staged reindex: reindex into a new index version, run validation queries, then swap.
- Keep an index-metadata table in Postgres/SQLite that records index versions, ingest timestamps, and embedding model id used.

Backups & restore
- Backup Postgres (or SQLite copy) and Faiss index files regularly. Provide `tools/backup_local.py` for local backups and a documented restore procedure.
- For S3-backed storage, enable object versioning and lifecycle rules to prevent accidental deletions.

Deployment & rollout strategies
- Use blue/green or canary deployments for backend and model-serving layers. Start with a single replica in prod, smoke-test, then increase replicas.
- For model changes, test new model images in a staging namespace and run a small suite of validation prompts before routing production traffic.

Load & chaos testing
- Create small load-testing scripts to simulate concurrent ingestion and query workloads. Measure Faiss, embedder, and model latency separately.
- Run occasional chaos tests (kill a model worker, simulate high-latency S3) in staging to validate resilience.

Operational checklist to advance stages (quick)
1. Tests + smoke: pass local E2E tests with a tiny model and reindex scripts.
2. Staging: deploy with Postgres + S3, run migration, run synthetic load (10–100 qps) and validate metrics.
3. Canary: deploy model change to 5–10% of traffic, run validation prompts, monitor error rates.
4. Scale: increase replicas or model workers based on measured bottlenecks (embedding CPU, Faiss latency, model throughput).

Section: Approach to configuration (env, files, secrets, local overrides)
----------------------------------------------------------------

Goal: keep configuration simple and 12-factor friendly while making it easy for students to run locally and for ops to lock down secrets in production.

Principles (KISS)
- Configuration should be environment-driven first (env vars). Provide a `.env.example` and document required/optional keys.
- Support a small `Settings` / config module in the backend (e.g., Pydantic BaseSettings) that reads from env and a local `.env` in dev.
- Keep secrets out of the repo. Use Kubernetes Secrets, a cloud secret manager, or CI secrets for production.

Recommended variables (minimal)
- MODE=local|prod
- DATABASE_URL (Postgres or sqlite URL)
- SECRET_KEY (crypto signing / session secret)
- S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY
- FAISS_INDEX_DIR, UPLOADS_DIR
- MODEL_PATH (path or key for the default model)
- EMBEDDING_MODEL (path or id)
- LOG_LEVEL (INFO/DEBUG/WARN)

Config precedence (explicit order)
1. Explicit function arguments (when calling tools/scripts)
2. Environment variables (process env)
3. Local `.env` file loaded in dev only (documented but optional)
4. Defaults in code

Local dev experience
- Provide `.env.example` with sensible defaults for local runs (MODE=local, UPLOADS_DIR=./data/uploads, FAISS_INDEX_DIR=./data/indexes).
- Support a `--config` flag for CLI tools to load a local YAML/JSON file for advanced testing scenarios.
- Keep `MODE=local` default behavior non-secret: do not require `SECRET_KEY` for local dev, but warn in logs if missing.

Secrets and production
- Do not commit secrets. Document how to provide secrets in Docker Compose (use `.env` or `docker compose --env-file`) and in k8s (create `Secret` objects or use Vault/managed secret stores).
- For CI, store sensitive values in Actions Secrets and inject them only for required jobs.

Runtime config best practices
- Centralize config parsing in `backend/app/core/settings.py` (or similar) and pass a single `settings` object to submodules. This reduces scatter and makes testing easier.
- Validate critical config at startup (fail fast if required values missing in `MODE=prod`).
- Expose a read-only `/config` or `/meta` endpoint only in non-production environments for debugging (never expose secrets).

Section: Approach to logging (structured logs, retention, local vs prod)
----------------------------------------------------------------

Goal: produce useful, searchable logs for debugging while keeping local runs simple and production logs structured for collection.

Principles
- Emit structured JSON logs to stdout in production so logs can be collected by the platform (Fluentd/Promtail/Logstash).
- For local dev, human-readable text logs are acceptable; make it easy to switch via `LOG_FORMAT=json|text`.
- Include minimal, consistent context on each request: timestamp, level, logger, request_id, path, method, status_code, latency_ms, user_id (if available).

Implementation hints (Python)
- Use the standard `logging` module or `structlog` for structured logs. A small wrapper module in `backend/app/core/logging.py` should:
  - configure the root logger from env vars (LOG_LEVEL, LOG_FORMAT)
  - add a request middleware to inject a `request_id` (UUID) into the logging context
  - ensure uvicorn/gunicorn is configured to use the same format

Retention and aggregation
- For local dev keep logs on stdout. For prod, push to a log collector (Promtail/Fluent Bit) and archive to long-term storage if required.
- Implement log rotation and retention policies at the collector or host level (don't rely on app-level file rotation unless necessary).

Alerting & errors
- Emit error-level logs with stack traces for unexpected exceptions; attach correlation ids for debugging (request_id).
- Export key error metrics to Prometheus (5xx count, exception rate) so alerts can be configured.

Privacy & verbosity
- Avoid logging full user-uploaded content or long document bodies. Log only metadata (document id, filename, size) unless debugging requires otherwise and is disabled in prod.
- Default to INFO in prod, DEBUG in developer mode.