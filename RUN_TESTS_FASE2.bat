@echo off
echo ========================================
echo FASE 2 - EJECUTAR TESTS UNITARIOS
echo ========================================
echo.

echo [1/3] Instalando dependencias de testing...
pip install pytest pytest-cov --quiet

echo.
echo [2/3] Ejecutando tests unitarios...
pytest tests/ -v --tb=short --cov=data-engine --cov-report=term-missing

echo.
echo [3/3] Generando reporte de cobertura...
pytest tests/ --cov=data-engine --cov-report=html

echo.
echo ========================================
echo TESTS COMPLETADOS
echo ========================================
echo.
echo Reporte HTML generado en: htmlcov/index.html
echo.
pause
