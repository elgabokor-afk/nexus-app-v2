@echo off
title NEXUS AI - FORCE UPDATE
color 0B
echo ==================================================
echo   FORCING MACHINE LEARNING UPGRADE
echo ==================================================
echo.
echo [1/3] upgrading pip...
python -m pip install --upgrade pip
echo.
echo [2/3] Installing Critical Brain Components...
python -m pip install joblib xgboost scikit-learn numpy pandas
echo.
echo [3/3] Verifying Installation...
python verify_ml_setup.py
echo.
echo ==================================================
echo   IF ALL IS GREEN, YOU ARE READY.
echo   IF RED, PLEASE SEND SCREENSHOT.
echo ==================================================
pause
