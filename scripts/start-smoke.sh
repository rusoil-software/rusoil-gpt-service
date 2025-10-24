#!/usr/bin/env bash
PORT=${1:-8000}
echo "Starting smoke server on http://0.0.0.0:$PORT"
python3 backend/smoke_server.py &
