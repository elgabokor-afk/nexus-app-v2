@echo off
echo Configurando deploy COMPLETO (todos los servicios)...
echo web: bash start_services.sh > Procfile
git add Procfile
git commit -m "Deploy full - All services"
git push
echo.
echo ✅ Deploy iniciado en Railway!
echo    Espera 2-3 minutos y revisa los logs.
pause
