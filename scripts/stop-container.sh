#!/usr/bin/env bash
NAME=${1:-usptu-local}
echo "Stopping container $NAME..."
docker rm -f $NAME || true
echo "Done."
