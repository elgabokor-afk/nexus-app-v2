@echo off
echo ========================================
echo   INICIANDO COSMOS AI WORKER
echo ========================================
echo.

echo [1/3] Verificando dependencias...
python -c "import ccxt, supabase, pandas" 2>nul
if errorlevel 1 (
    echo ERROR: Faltan dependencias
    echo Ejecutando: pip install -r requirements.txt
    pip install -r requirements.txt
)

echo.
echo [2/3] Verificando configuracion...
python check_ai_status.py

echo.
echo [3/3] Iniciando worker...
echo.
echo IMPORTANTE: Este proceso debe mantenerse corriendo
echo Para detenerlo, presiona Ctrl+C
echo.
pause

cd data-engine
python cosmos_worker.py
