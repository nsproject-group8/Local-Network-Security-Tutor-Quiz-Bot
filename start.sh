#!/bin/bash

# Start script for Network Security Tutor Bot

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Network Security Tutor & Quiz Bot${NC}"
echo "===================================="
echo ""

# Check if Ollama is running (non-blocking) — warn if not available
echo -e "${BLUE}Checking Ollama service...${NC}"
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${RED}⚠ Ollama not detected on localhost:11434. The app can run without Ollama but some features will be limited.${NC}"
    echo "If you need full functionality, start Ollama in a separate terminal:"
    echo "  ollama serve"
fi

# Function to start backend
start_backend() {
    echo ""
    echo -e "${BLUE}Starting Backend Server...${NC}"

    # Ensure venv exists
    if [ ! -d "venv" ]; then
        echo "Creating virtualenv..."
        python3 -m venv venv
    fi

    # Activate venv
    # shellcheck disable=SC1091
    source venv/bin/activate

    # Install dependencies if missing
    if [ ! -f "venv/.packages_installed" ]; then
        echo "Installing Python dependencies (this may take a while)..."
        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
        touch venv/.packages_installed
    fi

    cd backend || return
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    cd ..
}

# Function to start frontend
start_frontend() {
    echo ""
    echo -e "${BLUE}Starting Frontend Server...${NC}"
    cd frontend || return

    # Install deps if node_modules missing
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm ci
    fi

    npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    cd ..
}

# Start both services
start_backend
sleep 3  # Wait for backend to initialize (adjust if slow)
start_frontend

echo ""
echo -e "${GREEN}✨ Application started successfully!${NC}"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
