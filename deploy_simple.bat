@echo off
echo Configurando deploy SIMPLE (API + Worker)...
echo web: bash start_services_simple.sh > Procfile
git add Procfile
git commit -m "Deploy simple - API + Worker"
git push
echo.
echo ✅ Deploy iniciado en Railway!
echo    Espera 2-3 minutos y revisa los logs.
pause
