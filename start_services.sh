#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "  NEXUS AI - RAILWAY DEPLOYMENT"
echo "=========================================="

# Navigate to data-engine directory
cd data-engine

# Function to check if a process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo "✅ $1 is running"
        return 0
    else
        echo "❌ $1 failed to start"
        return 1
    fi
}

# 1. INITIALIZATION PHASE
echo ""
echo "[1/6] Initializing AI Models..."
python -u force_retrain.py || echo "⚠️  Model training skipped (may already exist)"

echo ""
echo "[2/6] Loading Academic Knowledge..."
python -u seed_academic_knowledge.py || echo "⚠️  Academic seeding skipped (may already exist)"

# 2. START CORE SERVICES
echo ""
echo "[3/6] Starting Cosmos Worker (Signal Generator)..."
python -u cosmos_worker.py 2>&1 | tee /tmp/cosmos_worker.log &
WORKER_PID=$!
sleep 3
if ps -p $WORKER_PID > /dev/null; then
    echo "✅ Cosmos Worker started (PID: $WORKER_PID)"
else
    echo "❌ Cosmos Worker failed to start"
    cat /tmp/cosmos_worker.log
fi

echo ""
echo "[4/6] Starting AI Oracle..."
python -u cosmos_oracle.py 2>&1 | tee /tmp/cosmos_oracle.log &
ORACLE_PID=$!
sleep 2
if ps -p $ORACLE_PID > /dev/null; then
    echo "✅ AI Oracle started (PID: $ORACLE_PID)"
else
    echo "⚠️  AI Oracle failed (non-critical)"
fi

echo ""
echo "[5/6] Starting Macro Feed..."
python -u macro_feed.py 2>&1 | tee /tmp/macro_feed.log &
MACRO_PID=$!
sleep 2
if ps -p $MACRO_PID > /dev/null; then
    echo "✅ Macro Feed started (PID: $MACRO_PID)"
else
    echo "⚠️  Macro Feed failed (non-critical)"
fi

echo ""
echo "[6/6] Starting Nexus Executor..."
python -u nexus_executor.py 2>&1 | tee /tmp/nexus_executor.log &
EXECUTOR_PID=$!
sleep 2
if ps -p $EXECUTOR_PID > /dev/null; then
    echo "✅ Nexus Executor started (PID: $EXECUTOR_PID)"
else
    echo "⚠️  Nexus Executor failed (non-critical)"
fi

# 3. START API GATEWAY (FOREGROUND)
echo ""
echo "=========================================="
echo "  STARTING NEXUS UNIFIED API"
echo "  Port: ${PORT:-8080}"
echo "=========================================="
echo ""

# Trap to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $WORKER_PID $ORACLE_PID $MACRO_PID $EXECUTOR_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start API Gateway (this keeps the container alive)
uvicorn nexus_api:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info

# If API exits, cleanup
cleanup
