@echo off
echo Configurando deploy MINIMO (solo API)...
echo web: bash start_minimal.sh > Procfile
git add Procfile
git commit -m "Deploy minimal - API only"
git push
echo.
echo ✅ Deploy iniciado en Railway!
echo    Espera 2-3 minutos y revisa los logs.
pause
