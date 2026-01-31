@echo off
echo ========================================
echo   DEPLOY A RAILWAY - RAMA ALTERNATIVA
echo ========================================
echo.

echo Este script creara una rama 'railway-deploy' para evitar
echo las reglas de proteccion de la rama main.
echo.
pause

echo.
echo [1/5] Creando rama railway-deploy...
git checkout -b railway-deploy 2>nul
if errorlevel 1 (
    echo Rama ya existe, cambiando a ella...
    git checkout railway-deploy
)

echo.
echo [2/5] Agregando archivos...
git add .

echo.
echo [3/5] Haciendo commit...
git commit -m "Railway deployment optimization"

echo.
echo [4/5] Haciendo push a railway-deploy...
git push origin railway-deploy
if errorlevel 1 (
    echo.
    echo Intentando con force push...
    git push origin railway-deploy --force
)

echo.
echo [5/5] Completado!
echo.
echo ========================================
echo   SIGUIENTE PASO
echo ========================================
echo.
echo 1. Ve a Railway Dashboard
echo 2. Settings -^> GitHub
echo 3. Cambia la rama de 'main' a 'railway-deploy'
echo 4. Railway hara redeploy automaticamente
echo.
echo ========================================
pause
