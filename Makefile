.PHONY: smoke build docker-run docker-stop

# Start the lightweight smoke server (for local dev)
smoke:
	python backend/smoke_server.py

# Build docker image
build:
	docker build -t petra-gpt-service:local .

# Run the image (default CMD) in detached mode
docker-run:
	docker run -d --name petra-gpt-local -p 8000:8000 petra-gpt-service:local || true

docker-stop:
	docker rm -f petra-gpt-local || true

# PowerShell helpers (callable from Git Bash/WSL via winpty or just use scripts/)
ps-build-and-run:
	@powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-and-run.ps1

ps-smoke:
	@powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-smoke.ps1

