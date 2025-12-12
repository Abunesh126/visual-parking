#!/bin/bash
# Linux/macOS Startup Script for Mall Parking System

echo "========================================"
echo "   Mall Parking System - Startup Script"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

# Check if Node.js is available  
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed or not in PATH"
    echo "Please install Node.js 16+ from your package manager"
    exit 1
fi

# Check if MySQL/MariaDB is running
if ! pgrep -x "mysqld" > /dev/null; then
    echo "WARNING: MySQL/MariaDB may not be running"
    echo "Please ensure your database server is started"
    echo ""
fi

echo "Starting Mall Parking System..."
echo ""

# Function to start backend
start_backend() {
    cd "$(dirname "$0")/parking-backend"
    echo "[1/3] Starting Backend Server..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and start
    source venv/bin/activate
    
    # Install dependencies if requirements.txt is newer
    if [ requirements.txt -nt venv/pyvenv.cfg ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    
    echo "Starting FastAPI server..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to start frontend
start_frontend() {
    cd "$(dirname "$0")/dashboard"
    echo "[2/3] Starting Dashboard..."
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
        echo "Installing Node.js dependencies..."
        npm install
    fi
    
    echo "Starting React development server..."
    npm start
}

# Function to start CV system
start_cv_system() {
    cd "$(dirname "$0")/parking-backend"
    if [ -f "app/cv/cv_service.py" ]; then
        echo "[3/3] Starting CV System..."
        source venv/bin/activate
        python app/cv/cv_service.py
    else
        echo "CV System files not found, skipping..."
    fi
}

# Start services in background
echo "Starting services..."

# Start backend in background
(start_backend) &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend in background  
(start_frontend) &
FRONTEND_PID=$!

# Start CV system in background
(start_cv_system) &
CV_PID=$!

echo ""
echo "========================================"
echo "   System Starting - Please Wait..."
echo "========================================"
echo ""
echo "Services will be available at:"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"  
echo "  • Dashboard: http://localhost:3000"
echo "  • Health Check: http://localhost:8000/health"
echo ""
echo "Process IDs:"
echo "  • Backend: $BACKEND_PID"
echo "  • Frontend: $FRONTEND_PID" 
echo "  • CV System: $CV_PID"
echo ""
echo "To stop the system, run: kill $BACKEND_PID $FRONTEND_PID $CV_PID"
echo "Or press Ctrl+C and use 'killall python3 node' if needed"
echo ""

# Wait for user input
echo "Press Enter to open the dashboard..."
read

# Open dashboard in default browser (Linux/macOS)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
else
    echo "Please open http://localhost:3000 in your browser"
fi

echo ""
echo "System started successfully!"
echo "For troubleshooting, check the README.md file"
echo ""

# Keep script running
wait