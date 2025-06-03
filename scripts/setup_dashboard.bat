
@echo off
echo ========================================
echo Audico Product Management System
echo Dashboard Setup
echo ========================================
echo.

cd /d "%~dp0\..\audico_dashboard\app"

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo Checking npm installation...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not available
    echo Please reinstall Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo Node.js found. Installing dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ========================================
echo Dashboard setup completed successfully!
echo ========================================
echo.
echo To start the dashboard:
echo   npm run dev
echo.
echo Dashboard will be available at: http://localhost:3000
echo.
echo Starting dashboard now...
echo Press Ctrl+C to stop the dashboard
echo.
npm run dev
