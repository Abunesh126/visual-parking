@echo off
echo 🚗 Starting Parking Management System...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  No .env file found. Creating from template...
    copy .env.example .env
    echo ✏️  Please edit .env file with your database credentials
    pause
)

REM Start the FastAPI server
echo 🚀 Starting FastAPI server...
echo 📖 API Documentation will be available at: http://localhost:8000/docs
echo 🏥 Health check available at: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server

cd parking-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause