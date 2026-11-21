@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Social Analyzer v2 - Viral Script Intelligence Hub

echo ===================================================================
echo              SOCIAL ANALYZER v2 - SISTEMA LOCAL-FIRST
echo         Metodo ACE: Analizar, Crear, Escalar (Localhost)
echo ===================================================================
echo.

:: 1. Verificar archivo de variables de entorno
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Configurando archivo .env desde plantilla .env.example...
        copy ".env.example" ".env" >nul
        echo [!] IMPORTANTE: Agrega tu APIFY_API_TOKEN y GEMINI_API_KEY en .env
    ) else (
        echo [ERROR] No se encontro .env ni .env.example en "%~dp0".
        pause
        exit /b 1
    )
) else (
    echo [OK] Archivo .env detectado.
)

:: 2. Verificar e inicializar entorno virtual de Python
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creando entorno virtual Python .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual de Python. Verifica que Python este instalado y en el PATH.
        pause
        exit /b 1
    )
    echo [*] Instalando dependencias del Backend...
    ".venv\Scripts\pip.exe" install -r backend\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Fallo la instalacion de dependencias de Python.
        pause
        exit /b 1
    )
) else (
    echo [OK] Entorno virtual Python listo.
)

:: 3. Verificar dependencias de Node.js en Frontend
if not exist "frontend\node_modules" (
    echo [*] Instalando dependencias del Frontend con npm install...
    pushd frontend
    call npm install
    if errorlevel 1 (
        popd
        echo [ERROR] Fallo la instalacion de dependencias de Node.js.
        pause
        exit /b 1
    )
    popd
) else (
    echo [OK] Dependencias de Frontend listas.
)

:: 4. Crear carpetas data y tmp_media si no existen
if not exist "data" mkdir data
if not exist "tmp_media" mkdir tmp_media

:: 5. Detectar puertos libres para Backend (desde 8000) y Frontend (desde 3000)
echo [*] Verificando puertos libres...
set "BACKEND_PORT=8000"
:find_backend_port
netstat -ano | findstr /R /C:":!BACKEND_PORT! .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    set /a BACKEND_PORT+=1
    goto find_backend_port
)

set "FRONTEND_PORT=3000"
:find_frontend_port
if "!FRONTEND_PORT!"=="!BACKEND_PORT!" (
    set /a FRONTEND_PORT+=1
    goto find_frontend_port
)
netstat -ano | findstr /R /C:":!FRONTEND_PORT! .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    set /a FRONTEND_PORT+=1
    goto find_frontend_port
)

echo [OK] Puerto libre asignado para Backend:  !BACKEND_PORT!
echo [OK] Puerto libre asignado para Frontend: !FRONTEND_PORT!

echo.
echo ===================================================================
echo [*] Iniciando Servidor Backend (FastAPI en http://localhost:!BACKEND_PORT!)...
echo [*] Iniciando Servidor Frontend (Vite en http://localhost:!FRONTEND_PORT!)...
echo ===================================================================
echo.

:: Lanzar Backend en ventana independiente con directorio de trabajo explicito
start "Social Analyzer v2 - Backend (FastAPI :!BACKEND_PORT!)" /D "%~dp0backend" cmd /k "..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port !BACKEND_PORT! --reload"

:: Esperar a que el Backend inicie
timeout /t 2 /nobreak >nul

:: Lanzar Frontend en ventana independiente con puertos sincronizados
start "Social Analyzer v2 - Frontend (Vite :!FRONTEND_PORT!)" /D "%~dp0frontend" cmd /k "set VITE_PORT=!FRONTEND_PORT!&& set VITE_API_PORT=!BACKEND_PORT!&& npm run dev -- --port !FRONTEND_PORT!"

:: Esperar a que el Frontend este listo y abrir navegador predeterminado
timeout /t 3 /nobreak >nul
start "" "http://localhost:!FRONTEND_PORT!"

echo [EXITO] Social Analyzer v2 iniciado correctamente.
echo - Frontend:              http://localhost:!FRONTEND_PORT!
echo - Backend API:           http://localhost:!BACKEND_PORT!
echo - Documentacion OpenAPI: http://localhost:!BACKEND_PORT!/docs
echo.
echo Para detener el sistema, simplemente cierra las ventanas de terminal.
pause
