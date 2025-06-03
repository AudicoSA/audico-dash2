
@echo off
echo ========================================
echo Audico Product Management System
echo System Launcher
echo ========================================
echo.

echo Starting Audico Product Management System...
echo.

echo [1/2] Starting Python backend...
cd /d "%~dp0\..\audico_product_manager"

if not exist venv (
    echo ERROR: Python virtual environment not found
    echo Please run install_python.bat first
    pause
    exit /b 1
)

if not exist .env (
    echo WARNING: .env file not found
    echo Please copy .env.example to .env and configure your credentials
    echo.
)

start "Audico Python Backend" cmd /k "venv\Scripts\activate.bat && python orchestrator.py"

echo [2/2] Starting Dashboard...
cd /d "%~dp0\..\audico_dashboard\app"

if not exist node_modules (
    echo ERROR: Node.js dependencies not found
    echo Please run setup_dashboard.bat first
    pause
    exit /b 1
)

timeout /t 3 /nobreak >nul
start "Audico Dashboard" cmd /k "npm run dev"

echo.
echo ========================================
echo System started successfully!
echo ========================================
echo.
echo Services running:
echo - Python Backend: Check the Python Backend window
echo - Dashboard: http://localhost:3000
echo.
echo To stop the system:
echo - Close both command windows
echo - Or press Ctrl+C in each window
echo.
echo Opening dashboard in browser...
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo System is now running. Check the opened windows for status.
pause
