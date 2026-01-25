@echo off
TITLE Nexus Launcher
color 0A

echo ==================================================
echo      NEXUS AUTONOMOUS TRADING ENGINE (LOCAL)
echo ==================================================
echo.
echo [1/3] Starting Market Scanner...
start "Nexus ScannerV2" cmd /k "cd data-engine && python scanner.py"

echo [2/3] Starting Paper Trader...
start "Nexus Paper Trader" cmd /k "cd data-engine && python paper_trader.py"

echo [3/3] Starting WebSocket Bridge...
start "Nexus WS Bridge" cmd /k "cd data-engine && python websocket_bridge.py"

echo.
echo [SUCCESS] All systems active. 
echo Checks:
echo  - Scanner: Watching 5m/1h Candles
echo  - Trader:  Monitoring Portfolio & Redis
echo  - Bridge:  Relaying to ws://localhost:8000
echo.
echo You can minimize these windows, but do not close them.
echo.
pause
