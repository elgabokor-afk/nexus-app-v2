@echo off
title NEXUS NEURAL LINK (Python Engine)
color 0A
echo ==================================================
echo   INITIALIZING COSMOS NEURAL LINK...
echo ==================================================
echo.
echo [INFO] Killing any zombie processes on Port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo [INFO] Port 8000 Cleared.
echo.
echo [INFO] Starting Cosmos Agent...
cd data-engine
python websocket_bridge.py
pause
