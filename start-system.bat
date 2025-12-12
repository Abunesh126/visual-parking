@echo off
REM Windows Startup Script for Mall Parking System
echo ========================================
echo   Mall Parking System - Startup Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

REM Check if MySQL is running
echo Checking MySQL service...
sc query mysql >nul 2>&1
if errorlevel 1 (
    echo WARNING: MySQL service not found. Please ensure MySQL is installed and running.
    echo Database setup may be required.
    echo.
)

echo Starting Mall Parking System...
echo.

REM Start backend in new window
echo [1/3] Starting Backend Server...
start "Mall Parking - Backend" /D "%~dp0parking-backend" cmd /k "echo Activating virtual environment... && venv\Scripts\activate && echo Starting FastAPI server... && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend in new window
echo [2/3] Starting Dashboard...
start "Mall Parking - Dashboard" /D "%~dp0dashboard" cmd /k "echo Installing dependencies if needed... && npm install --silent && echo Starting React development server... && npm start"

REM Start computer vision system (if available)
echo [3/3] Starting CV System...
if exist "%~dp0parking-backend\app\cv\cv_service.py" (
    start "Mall Parking - CV System" /D "%~dp0parking-backend" cmd /k "venv\Scripts\activate && echo Starting Computer Vision System... && python app\cv\cv_service.py"
) else (
    echo CV System files not found, skipping...
)

echo.
echo ========================================
echo   System Starting - Please Wait...
echo ========================================
echo.
echo Services will be available at:
echo   • Backend API: http://localhost:8000
echo   • API Docs: http://localhost:8000/docs
echo   • Dashboard: http://localhost:3000
echo   • Health Check: http://localhost:8000/health
echo.
echo Press any key to open the dashboard...
pause >nul

REM Open dashboard in default browser
start http://localhost:3000

echo.
echo System started successfully!
echo.
echo To stop the system:
echo   1. Close all command windows
echo   2. Or press Ctrl+C in each window
echo.
echo For troubleshooting, check the README.md file
pause