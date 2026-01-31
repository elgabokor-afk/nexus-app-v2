@echo off
set "SCRIPT_PATH=%~dp0NEXUS_DEPLOY.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"
pause
