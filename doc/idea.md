## rusoil-gpt-service — Idea and Design

Purpose
-------
rusoil-gpt-service is a Dockerized AI service providing modern AI features to university students and researchers. It exposes a simple chatbot web form and APIs for advanced features including:

- Vibe-coding (AIDD, agent-driven coding assistants)
- Agent AI orchestration (multi-step autonomous agents)
- Deep thinking & advanced problem-solving workflows
- Visual data processing (image/video understanding, diagram interpretation)

The system must be usable in two primary modes:

- Compact / local: runs on a student's laptop or home server (single-node, CPU or small GPU). Easy to install and run via Docker.
- Scalable / pro: production-grade, multi-user system capable of scaling to very high concurrency (target design goal: up to 1M concurrent requests) using cloud-native infrastructure.

High-level contract
-------------------
- Input: JSON requests or websocket messages containing prompt, modality (text/image), optional context/meta (student id, course id), and request parameters (temperature, max_tokens, agent mode).
- Output: structured JSON (text responses, agent actions, status codes) and streaming websocket updates for incremental responses.
- Error modes: validation errors (400), auth/permission (401/403), model server unavailable (503), rate-limited (429), internal errors (500).

Core requirements and non-functional goals
---------------------------------------
- Usability: one-command Docker run for local mode; simple web/chat UI.
- Extensibility: support multiple models (open-source & hosted APIs), plugins for new modalities.
- Privacy & safety: per-university data governance, opt-in logging, student SSO support.
- Performance & scalability: low-latency interactive responses for individual users; horizontal scaling and batching for throughput.
- Cost-awareness: provide CPU-only, quantized model options for local use and GPU/cluster options for cloud.

Suggested tech stack (MVP)
-------------------------
- Backend API: FastAPI (Python) with Uvicorn/ASGI for async handling.
- Web UI: small React or plain HTML+JS single-page app with websocket support for streaming.
- Model serving:
  - Local / small: GGML-style CPU models (quantized) using llama.cpp bindings, or llama.cpp + Flask/FastAPI wrapper.
  - Production: Triton Inference Server / Ray Serve / TorchServe, or managed endpoints (Cloud AICore) depending on model.
- Cache & queue: Redis for short-term caching, rate-limits, and pub/sub for streaming.
- Persistence: PostgreSQL for metadata and user records (optional for strict local mode).
- Containerization: Dockerfile for local/prototype image; Helm charts / Kustomize for Kubernetes.

Architecture overview
---------------------

1) Edge / Client
- Static web UI served by CDN or simple NGINX.
- Websocket or HTTP long-poll for chat streaming.

2) API Gateway / Ingress
- Auth, TLS termination, rate limiting, request routing.

3) Frontend Service (FastAPI)
- Auth & session management (SSO/Uni login), request validation, per-request orchestration.
- Lightweight orchestration of multi-step agent flows.
- Send/receive messages to model-serving layer (sync or async).

4) Model Serving Layer
- One or multiple model servers, specialized by modality (text, vision, multimodal).
- For production: autoscaling GPU nodes, batching, and sharding. For local: single quantized CPU model.

5) Supporting Services
- Redis: caching, rate limiting, pub/sub for streaming.
- PostgreSQL: user/course metadata, audit logs (optional/controlled).
- Object storage (S3 or local) for larger inputs like videos/images.
- Observability: Prometheus, Grafana, ELK or Loki for logs.

Scalability strategy (from laptop -> 1M concurrent requests)
---------------------------------------------------------

Local / Small
- Single Docker container with a small quantized model. Prioritize low RAM usage.
- Low concurrency (tens of concurrent websocket clients). Use CPU-optimized inference (GGML).

Mid-size / University cluster
- Kubernetes cluster with multiple replicas of the frontend and model servers.
- Redis & Postgres managed services.
- Horizontal Pod Autoscaler (HPA) on API and model-serving components.

High-scale / 1M concurrent requests (architectural guidelines and caveats)
- 1M truly concurrent active model inference requests is extremely large — clarify what "concurrent" means (open websocket connections vs. actively processing inference). Design assumes a mix of idle connections + burst inference.
- Use an edge layer + CDN for static assets to reduce load.
- Use a resilient ingress/API Gateway (e.g., Nginx, Envoy, or cloud API GW) with connection multiplexing.
- Shard workload across many model servers; put a lightweight orchestrator that dispatches to specialized model clusters (text-only, vision-only, large-models).
- Use batching and request aggregation for throughput efficiency. Employ model quantization and mixed precision for cost savings.
- Use autoscaling groups of GPU nodes with spot/ondemand mixture and pre-warm mechanisms.
- Consider serverless inference platforms for burst isolation (where available).
- Implement aggressive caching for deterministic responses, and per-student rate limits/quotas.

Key horizontal scaling techniques
- Async, non-blocking request handling; stream partial responses.
- Batching at model server level.
- Prioritized queues for interactive vs. background work.
- Backpressure and graceful degradation (fallback to smaller/quantized models or queued responses).

Security, privacy and governance
--------------------------------
- Student authentication through university SSO (OAuth2/OpenID Connect). Local mode can run without SSO but must warn about differences.
- Consent and data retention policy: only store logs for debugging when enabled; store sensitive data encrypted.
- Per-tenant isolation: separate namespaces / model instances or strict RBAC.
- Rate limiting & abuse detection. Content filtering (safety classifiers) for student-facing features.

Model & data choices
---------------------
- Start with open-source LLMs (Llama-family, Mistral, or Llama 3 variants where license permits) and open multimodal models for vision tasks.
- Provide adapters for hosted APIs (OpenAI, Anthropic, Azure, etc.) so universities can choose.
- For vibe-coding (AIDD/agent workflows), build a small orchestration layer that can call code execution sandboxes, run unit tests, or create diffs.
- For visual data processing, use specialized vision models (Segment Anything, Stable Diffusion for generative workflows, Detectron2/YOLO for detection) depending on tasks.

Developer UX and local-first priority
------------------------------------
- One-command local start: docker build . && docker run -p 8000:8000 rusoil-gpt-service
- Provide a toggled configuration: local (CPU quantized), hybrid (use remote model APIs), and cloud (production endpoints).
- Clear docs for adding a new model plugin and for switching between local and cloud models.

Testing and quality gates
-------------------------
- Unit tests for API, auth, and orchestration logic.
- Integration tests for end-to-end chat flows (including streaming websocket tests).
- Load tests and chaos tests:
  - Simulate many idle websockets + bursty inference.
  - Validate degradation strategies and fallback.
- Security tests: SSO flows, RBAC, injection attempts, and data leakage checks.

Edge cases and risks
--------------------
- Model licensing or export restrictions: ensure chosen models allow intended use.
- Cost blowout: GPU-based inference at scale is expensive; implement quotas and cost-aware routing.
- Latency: large models may add unacceptable latency for interactive use. Provide fallbacks to smaller models.
- Data privacy: storing student submissions needs clear policies and consent.

Roadmap (MVP → Production)
--------------------------
MVP (0–4 weeks)
- Minimal FastAPI backend + simple web chat UI.
- Local-mode Dockerfile using a small quantized model or proxy to a hosted API.
- Basic auth (optional local login) and simple safety filter.

Phase 1 (1–3 months)
- Model plugin system; support for one open-source LLM and one hosted API provider.
- Redis caching, simple Postgres metadata, basic Observability.
- Tests: unit + basic integration.

Phase 2 (3–6 months)
- Kubernetes deployment manifests / Helm chart, autoscaling, model-serving via Triton or Ray Serve.
- Agent orchestration features for vibe-coding (code execution sandbox, test runner integration).
- Visual processing pipelines (image upload + inference + visualization).

Phase 3 (6+ months)
- Production hardening: multi-region, API gateway, advanced autoscaling, advanced batching.
- Cost controls, quota management, academic integrations (LMS plugins), fine-grained RBAC.

Operational considerations & SRE playbook
---------------------------------------
- Observability: traces (OpenTelemetry), metrics (Prometheus), logs (structured JSON), dashboards for latency, error rates, model queue depth.
- Incident response: fallback model, kill-switch, traffic throttles.
- Backups & migrations: DB backups, model artifact versioning.

Suggested next steps (concrete)
-------------------------------
1. Review this draft and confirm priorities (local-first vs immediate cloud).  
2. Agree MVP tech choices (quantized local model vs hosted API for initial backend).  
3. I can scaffold a minimal Dockerized FastAPI + simple web chat UI implementation (proposed next todo).  

Contact & notes
---------------
Keep this document as the living product idea in `doc/idea.md`. When decisions are made (e.g., which models to use, SSO integration details), append configuration choices and license notes here.

Quality gates / acceptance criteria for the doc
---------------------------------------------
- Covers user story and primary use-cases (student local use, university-grade scale).  
- Includes an MVP plan with a clear minimal runnable container.  
- Outlines production scaling constraints and concrete techniques to approach 1M concurrent requests (with caveats).  
- Lists security and privacy constraints for student data.

-- End of idea document
