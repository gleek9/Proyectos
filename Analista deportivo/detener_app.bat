@echo off
title Detener Katakuri AI
echo =====================================================================
echo           DETENIENDO SERVIDORES DE KATAKURI AI
echo =====================================================================
echo.
echo Cerrando procesos de Uvicorn/Python en puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a 2>nul
)

echo Cerrando procesos de Vite/Node en puerto 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a 2>nul
)

echo.
echo [OK] Servidores detenidos correctamente.
timeout /t 2 > nul
exit
