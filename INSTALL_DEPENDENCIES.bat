@echo off
REM ============================================================================
REM COSMOS AI - Instalador de Dependencias Semana 2
REM Ejecutar como: INSTALL_DEPENDENCIES.bat
REM ============================================================================

echo.
echo ========================================
echo  COSMOS AI - Instalacion Semana 2
echo ========================================
echo.

REM Verificar que Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en PATH
    echo Por favor instala Python 3.9+ desde https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detectado
python --version
echo.

REM Verificar que pip esta instalado
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip no esta instalado
    echo Instalando pip...
    python -m ensurepip --upgrade
)

echo [OK] pip detectado
python -m pip --version
echo.

echo ========================================
echo  Instalando dependencias criticas...
echo ========================================
echo.

REM Actualizar pip
echo [1/5] Actualizando pip...
python -m pip install --upgrade pip

REM Instalar ratelimit (Fix 5)
echo [2/5] Instalando ratelimit (proteccion API)...
python -m pip install ratelimit

REM Instalar structlog (Fix 8)
echo [3/5] Instalando structlog (logging estructurado)...
python -m pip install structlog python-json-logger

REM Instalar pytest (Fix 7)
echo [4/5] Instalando pytest (testing)...
python -m pip install pytest pytest-cov pytest-mock

REM Instalar herramientas de calidad
echo [5/5] Instalando herramientas de calidad...
python -m pip install radon

echo.
echo ========================================
echo  Verificando instalacion...
echo ========================================
echo.

REM Verificar instalaciones
python -c "import ratelimit; print('[OK] ratelimit instalado')" 2>nul || echo [ERROR] ratelimit fallo
python -c "import structlog; print('[OK] structlog instalado')" 2>nul || echo [ERROR] structlog fallo
python -c "import pytest; print('[OK] pytest instalado')" 2>nul || echo [ERROR] pytest fallo
python -c "import radon; print('[OK] radon instalado')" 2>nul || echo [ERROR] radon fallo

echo.
echo ========================================
echo  Instalacion completada!
echo ========================================
echo.
echo Proximos pasos:
echo 1. Ejecutar indices en Supabase (ver EJECUTAR_INDICES_SUPABASE.md)
echo 2. Ejecutar tests: pytest tests/ -v
echo 3. Verificar logs: python data-engine/cosmos_worker.py
echo.

pause
