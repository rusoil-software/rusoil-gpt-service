#!/usr/bin/env bash
TAG=${1:-rusoil-gpt-service:local}
PORT=${2:-8000}
echo "Building image $TAG..."
docker build -t $TAG .
echo "Running container $TAG on port $PORT..."
docker run -d --name usptu-local -p ${PORT}:8000 $TAG || true
echo "Container started (if build succeeded)."
