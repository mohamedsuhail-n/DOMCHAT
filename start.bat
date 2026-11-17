@echo off
title DOMCHAT Launcher
color 0B
echo ============================================================
echo                     DOMCHAT LAUNCHER
echo      Local AI & Hybrid RAG Workstation (Intel i3 / 8GB RAM)
echo ============================================================
echo.

:: 1. Check Ollama
echo [1/4] Checking Ollama AI service...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Ollama is not running on http://127.0.0.1:11434.
    echo Attempting to start Ollama in the background...
    start "" ollama serve
    timeout /t 3 >nul
)

:: Verify qwen2.5:1.5b is installed
ollama list 2>nul | findstr "qwen2.5:1.5b" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Pre-installed model qwen2.5:1.5b not found in Ollama.
    echo Please run: ollama pull qwen2.5:1.5b
) else (
    echo [OK] Ollama connected and qwen2.5:1.5b verified.
)

:: 2. Check Python Virtual Environment
echo.
echo [2/4] Checking Python backend environment...
if not exist ".\venv\Scripts\python.exe" (
    echo Creating virtual environment with Python 3.11...
    py -3.11 -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt --prefer-binary
)
echo [OK] Python backend virtual environment ready.

:: 3. Check Frontend Dependencies
echo.
echo [3/4] Checking Frontend dependencies...
if not exist ".\frontend\node_modules" (
    echo Installing frontend packages...
    cd frontend && npm install && cd ..
)
echo [OK] Frontend ready.

:: 4. Start Services
echo.
echo [4/4] Starting DOMCHAT Backend and Frontend...
start "DOMCHAT Backend (Flask)" cmd /k ".\venv\Scripts\python.exe backend\app.py"
start "DOMCHAT Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================================
echo  DOMCHAT is starting!
echo  Backend:  http://127.0.0.1:5000/api
echo  Frontend: http://localhost:5173
echo ============================================================
echo.

timeout /t 3 >nul
start http://localhost:5173

pause
