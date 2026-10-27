@echo off
title Katakuri v4.0 - Plataforma de Prediccion Deportiva de Alta Precision
chcp 65001 > nul
cd /d "%~dp0"

echo =====================================================================
echo      INICIANDO KATAKURI v4.0 (ALTA PRECISION ^& DATOS REALES)
echo =====================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_app.py
) else (
    python run_app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion Katakuri v4.0.
    pause
)
