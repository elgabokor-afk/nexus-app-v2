@echo off
title NEXUS NEURAL LINK (STRICT MODE)
color 0A
echo ==================================================
echo   INITIALIZING COSMOS NEURAL LINK (STRICT)
echo ==================================================
echo.
echo [INFO] Using Verified Python Path:
echo C:\Users\NPC2\AppData\Local\Python\pythoncore-3.14-64\python.exe
echo.
echo [INFO] Killing any zombie processes on Port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo [INFO] Port 8000 Cleared.
echo.
echo [INFO] Starting Cosmos Agent...
cd data-engine
"C:\Users\NPC2\AppData\Local\Python\pythoncore-3.14-64\python.exe" websocket_bridge.py
pause
