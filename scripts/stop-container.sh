#!/usr/bin/env bash
NAME=${1:-rusoilgpt-local}
echo "Stopping container $NAME..."
docker rm -f $NAME || true
echo "Done."
