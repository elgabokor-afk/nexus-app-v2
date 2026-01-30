@echo off
REM ============================================================================
REM COSMOS AI - Ejecutar Tests de Semana 2
REM ============================================================================

echo.
echo ========================================
echo  COSMOS AI - Test Suite Semana 2
echo ========================================
echo.

REM Verificar que pytest está instalado
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [ERROR] pytest no esta instalado
    echo Instalando pytest...
    python -m pip install pytest pytest-cov pytest-mock
    echo.
)

echo [INFO] Ejecutando tests...
echo.

REM Opción 1: Tests básicos
echo ========================================
echo  OPCION 1: Tests Basicos
echo ========================================
python -m pytest tests/ -v

echo.
echo ========================================
echo  OPCION 2: Tests con Cobertura
echo ========================================
python -m pytest tests/ -v --cov=data-engine --cov-report=term

echo.
echo ========================================
echo  OPCION 3: Tests con Reporte HTML
echo ========================================
python -m pytest tests/ -v --cov=data-engine --cov-report=html

if exist htmlcov\index.html (
    echo.
    echo [OK] Reporte HTML generado en: htmlcov\index.html
    echo Abriendo reporte...
    start htmlcov\index.html
)

echo.
echo ========================================
echo  Tests Completados
echo ========================================
echo.

pause
