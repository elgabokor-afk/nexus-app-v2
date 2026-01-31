#!/bin/bash
set -e

echo "=========================================="
echo "  NEXUS AI - EMERGENCY DIAGNOSTIC MODE"
echo "=========================================="
echo ""

# Print all environment variables to diagnose
echo "[DIAGNOSTIC] Checking environment variables..."
echo "PORT: ${PORT}"
echo "PYTHONUNBUFFERED: ${PYTHONUNBUFFERED}"
echo "SUPABASE_URL exists: $([ -n "$SUPABASE_URL" ] && echo "YES" || echo "NO")"
echo "NEXT_PUBLIC_SUPABASE_URL exists: $([ -n "$NEXT_PUBLIC_SUPABASE_URL" ] && echo "YES" || echo "NO")"
echo "SUPABASE_SERVICE_ROLE_KEY exists: $([ -n "$SUPABASE_SERVICE_ROLE_KEY" ] && echo "YES" || echo "NO")"
echo "REDIS_URL exists: $([ -n "$REDIS_URL" ] && echo "YES" || echo "NO")"
echo ""

# Navigate to data-engine
cd data-engine || { echo "ERROR: data-engine directory not found"; exit 1; }

echo "[1/2] Starting Nexus API (Simplified Mode)..."
echo "Listening on port ${PORT:-8080}"
echo ""

# Start ONLY the API - skip all workers for now
exec uvicorn nexus_api:app --host 0.0.0.0 --port ${PORT:-8080} --log-level debug
