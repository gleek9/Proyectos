@echo off
title Katakuri AI - Sports Prediction Platform Launcher
chcp 65001 > nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_app.py
) else (
    python run_app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
