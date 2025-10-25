USPTU infra artifacts (minimal)
================================

What is here
- `docker-compose.prod.yml` — a small production-ish compose that runs `backend`, `model-worker`, and `postgres`. It's minimal and uses env vars for secrets.
- `k8s/` — small Kubernetes manifests for quick staging: `backend-deployment.yaml`, `model-worker-deployment.yaml`, and `postgres-deployment.yaml`.

Purpose and usage
- These artifacts are intentionally small and educational. They are useful for:
  - spinning up a quick staging environment
  - showing the minimal set of objects you'll need when moving to k8s
  - serving as starting points for CI/CD and infra tests

Quick start (docker-compose)
1. Copy `.env.example` to `.env` and set `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `S3_*` etc.
2. Build your image locally:

```powershell
docker build -t petra-gpt-service .
docker compose -f infra/docker-compose.prod.yml up --build
```

Quick start (k8s, local)
- For quick local testing you can use `minikube` or `kind`. Example using `kubectl` (assumes a cluster is available):

```powershell
# apply secrets (replace with secure tooling in prod)
kubectl create secret generic petra-gpt-secrets --from-literal=DATABASE_URL='postgres://petra-gpt:pass@petra-gpt-postgres-svc:5432/petra-gpt' --from-literal=POSTGRES_USER=petra-gpt --from-literal=POSTGRES_PASSWORD=petra-gpt_pass

# apply manifests
kubectl apply -f infra/k8s/postgres-deployment.yaml
kubectl apply -f infra/k8s/backend-deployment.yaml
kubectl apply -f infra/k8s/model-worker-deployment.yaml
```

Notes & next steps
- The Postgres manifest uses an `emptyDir` for brevity. Replace with a PVC for any persistent staging/production use.
- Add an `Ingress` manifest or load balancer rule if you want to expose services externally.
- Consider adding a simple Helm chart once you stabilize the runtime configuration.
