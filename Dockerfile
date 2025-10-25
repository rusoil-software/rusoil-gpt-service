# Multi-stage Dockerfile for petra-gpt-service (robust to missing frontend/backend)

# Stage 0: copy repo to a build area and optionally build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /src
COPY . /src
RUN apk add --no-cache bash \
    && if [ -d "frontend" ]; then \
             cd frontend && npm ci --silent && npm run build; \
         else \
             mkdir -p frontend/dist && echo '<!-- no frontend assets -->' > frontend/dist/index.html; \
         fi

# Stage 1: install python deps (poetry or requirements.txt fallback)
FROM python:3.11-slim AS deps
WORKDIR /src
COPY . /src
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc git curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN if [ -f "pyproject.toml" ]; then \
            pip install --no-cache-dir poetry==1.8.1 && \
            poetry config virtualenvs.create false && \
            poetry install --no-root --no-dev --no-interaction ; \
        elif [ -f "requirements.txt" ]; then \
            pip install --no-cache-dir -r requirements.txt ; \
        else \
            echo "No pyproject.toml or requirements.txt found — skipping Python deps install"; \
        fi

# Stage 2: runtime image
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates libsndfile1 bash && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from deps stage (if any)
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy backend source if present, else copy whole repo as fallback
COPY --from=deps /src /src
RUN if [ -d /src/backend ]; then \
            mkdir -p /app/backend && cp -r /src/backend/* /app/backend/ ; \
        else \
            mkdir -p /app/backend && cp -r /src/* /app/backend/ ; \
        fi

# Copy built frontend into a static directory (from frontend-build stage)
RUN if [ -d /src/frontend/dist ]; then \
            mkdir -p /app/backend/static && cp -r /src/frontend/dist/* /app/backend/static/ ; \
        else \
            mkdir -p /app/backend/static && echo '<!-- no frontend -->' > /app/backend/static/index.html ; \
        fi

ENV PYTHONUNBUFFERED=1
ENV MODE=local
WORKDIR /app/backend
EXPOSE 8000
# Default command: run uvicorn app.main:app; override in compose for model workers or other entrypoints
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
