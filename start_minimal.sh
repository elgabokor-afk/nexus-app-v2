#!/bin/bash

echo "=== NEXUS AI STARTING ==="
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "PORT: ${PORT:-8080}"
echo "=========================="

cd data-engine

echo "Starting API only (minimal mode)..."
python -u -m uvicorn nexus_api:app --host 0.0.0.0 --port ${PORT:-8080}
