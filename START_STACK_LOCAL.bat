@echo off
title NEXUS INSTITUTIONAL STACK (LOCAL)
color 0A

echo ===================================================
echo   NEXUS AI - PHASE 41 - INSTITUTIONAL LAUNCHER
echo ===================================================
echo.
echo [1/4] Checking Environment...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python 3.9+
    pause
    exit
)
echo Python OK.
echo.

echo [2/4] Starting Redis (Mock or Remote)...
echo NOTICE: Ensure Redis is running on port 6379 or set in .env.local
echo.

echo [3/4] Launching HOT LAYER (Stream Processor)...
start "Nexus Ingest (Hot Layer)" cmd /k "python data-engine/stream_processor.py"
echo Ingest Service Launched.

echo [4/4] Launching BRAIN (Cosmos Worker)...
start "Nexus Brain (Cosmos)" cmd /k "python data-engine/cosmos_worker.py"
echo Brain Service Launched.

echo.
echo ===================================================
echo   ALL SYSTEMS ONLINE. MONITOR WINDOWS FOR LOGS.
echo ===================================================
pause
