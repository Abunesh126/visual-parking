#!/bin/bash

# Parking Management System Startup Script

echo "🚗 Starting Parking Management System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your database credentials"
    read -p "Press Enter to continue after editing .env file..."
fi

# Start the FastAPI server
echo "🚀 Starting FastAPI server..."
echo "📖 API Documentation will be available at: http://localhost:8000/docs"
echo "🏥 Health check available at: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"

cd parking-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000