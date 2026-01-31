#!/bin/bash
set -e

echo "=========================================="
echo "  NEXUS AI - STARTING"
echo "=========================================="

cd data-engine || exit 1

echo "Starting Cosmos Worker..."
python -u cosmos_worker.py &
WORKER_PID=$!
echo "Worker PID: $WORKER_PID"

sleep 5

echo "Starting Nexus API on port ${PORT:-8080}..."
exec uvicorn nexus_api:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info
