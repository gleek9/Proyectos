@echo off
setlocal enabledelayedexpansion
title Social Analyzer v1.1 — Viral Script Intelligence Hub

echo ===================================================================
echo             SOCIAL ANALYZER v1.1 - SISTEMA LOCAL-FIRST
echo         Metodo ACE: Analizar, Crear, Escalar (Localhost)
echo ===================================================================
echo.

:: 1. Verificar archivo de variables de entorno
if not exist ".env" (
    echo [*] Configurando archivo .env desde plantilla .env.example...
    copy ".env.example" ".env" >nul
    echo [!] IMPORTANTE: Agrega tu APIFY_API_TOKEN y GEMINI_API_KEY en .env
) else (
    echo [OK] Archivo .env detectado.
)

:: 2. Verificar e inicializar entorno virtual de Python
if not exist ".venv\Scripts\activate.bat" (
    echo [*] Creando entorno virtual Python (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual de Python. Verifica que Python este instalado y en el PATH.
        pause
        exit /b 1
    )
    echo [*] Instalando dependencias del Backend...
    .\.venv\Scripts\pip install -r backend\requirements.txt
) else (
    echo [OK] Entorno virtual Python listo.
)

:: 3. Verificar dependencias de Node.js en Frontend
if not exist "frontend\node_modules" (
    echo [*] Instalando dependencias del Frontend (npm install)...
    cd frontend
    call npm install
    cd ..
) else (
    echo [OK] Dependencias de Frontend listas.
)

:: 4. Crear carpetas data y tmp_media si no existen
if not exist "data" mkdir data
if not exist "tmp_media" mkdir tmp_media

echo.
echo ===================================================================
echo [*] Iniciando Servidor Backend (FastAPI en http://localhost:8000)...
echo [*] Iniciando Servidor Frontend (Vite en http://localhost:3000)...
echo ===================================================================
echo.

:: Lanzar Backend en ventana independiente
start "Social Analyzer v1.1 - Backend (FastAPI)" cmd /k "cd backend && ..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Esperar 2 segundos a que el backend inicie
timeout /t 2 /nobreak >nul

:: Lanzar Frontend en ventana independiente
start "Social Analyzer v1.1 - Frontend (Vite)" cmd /k "cd frontend && npm run dev"

:: Esperar 2 segundos adicionales y abrir navegador predeterminado
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo [EXITO] Social Analyzer v1.1 iniciado correctamente.
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - Documentacion OpenAPI: http://localhost:8000/docs
echo.
echo Para detener el sistema, simplemente cierra las ventanas de terminal.
pause
