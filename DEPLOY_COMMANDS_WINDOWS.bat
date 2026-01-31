@echo off
echo ========================================
echo   DEPLOY A RAILWAY - COMANDOS WINDOWS
echo ========================================
echo.

echo Selecciona una opcion:
echo.
echo 1. Deploy version MINIMA (solo API)
echo 2. Deploy version SIMPLE (API + Worker)
echo 3. Deploy version COMPLETA (todos los servicios)
echo 4. Deploy con DIAGNOSTICO
echo.

set /p option="Ingresa el numero (1-4): "

if "%option%"=="1" (
    echo.
    echo Configurando version MINIMA...
    echo web: bash start_minimal.sh > Procfile
    git add Procfile
    git commit -m "Deploy minimal version - API only"
    git push
    echo.
    echo ✅ Deploy iniciado! Revisa los logs en Railway.
    goto end
)

if "%option%"=="2" (
    echo.
    echo Configurando version SIMPLE...
    echo web: bash start_services_simple.sh > Procfile
    git add Procfile
    git commit -m "Deploy simple version - API + Worker"
    git push
    echo.
    echo ✅ Deploy iniciado! Revisa los logs en Railway.
    goto end
)

if "%option%"=="3" (
    echo.
    echo Configurando version COMPLETA...
    echo web: bash start_services.sh > Procfile
    git add Procfile
    git commit -m "Deploy full version - All services"
    git push
    echo.
    echo ✅ Deploy iniciado! Revisa los logs en Railway.
    goto end
)

if "%option%"=="4" (
    echo.
    echo Configurando con DIAGNOSTICO...
    echo web: python railway_debug.py; bash start_minimal.sh > Procfile
    git add Procfile
    git commit -m "Deploy with diagnostic"
    git push
    echo.
    echo ✅ Deploy iniciado! Revisa los logs en Railway para ver el diagnostico.
    goto end
)

echo.
echo ❌ Opcion invalida
echo.

:end
pause
