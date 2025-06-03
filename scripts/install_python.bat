
@echo off
echo ========================================
echo Audico Product Management System
echo Python Environment Setup
echo ========================================
echo.

cd /d "%~dp0\..\audico_product_manager"

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ========================================
echo Python setup completed successfully!
echo ========================================
echo.
echo Virtual environment created at: %CD%\venv
echo To activate manually: venv\Scripts\activate.bat
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Configure your credentials in .env
echo 3. Run the dashboard setup: ..\scripts\setup_dashboard.bat
echo.
pause
