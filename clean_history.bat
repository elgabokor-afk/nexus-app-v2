@echo off
echo ========================================
echo   LIMPIAR HISTORIAL DE GIT
echo ========================================
echo.
echo ADVERTENCIA: Esto creara una rama nueva sin historial
echo Los commits anteriores se perderan
echo.
pause

echo.
echo Creando rama limpia...
git checkout --orphan clean-deploy

echo.
echo Agregando archivos...
git add .

echo.
echo Haciendo commit inicial...
git commit -m "Clean deployment - no secrets in history"

echo.
echo Eliminando rama anterior...
git branch -D railway-deploy

echo.
echo Renombrando rama...
git branch -m railway-deploy

echo.
echo Haciendo push (force)...
git push origin railway-deploy --force

echo.
echo ========================================
echo   COMPLETADO
echo ========================================
echo.
echo Ahora configura Railway para usar la rama 'railway-deploy'
echo.
pause
