#!/bin/bash

# Verification script to check if everything is set up correctly

echo "🔍 Network Security Tutor Bot - Installation Verification"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Function to check command
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check file
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check directory
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 directory exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 directory is missing"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo "Checking required commands..."
echo "-----------------------------"
check_command python3
check_command node
check_command npm
check_command ollama

echo ""
echo "Checking Python version..."
echo "-------------------------"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
    echo -e "${GREEN}✓${NC} Python $python_version (>= 3.9 required)"
else
    echo -e "${RED}✗${NC} Python $python_version (>= 3.9 required)"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Checking Node.js version..."
echo "--------------------------"
node_version=$(node --version 2>&1 | cut -d'v' -f2)
major=$(echo $node_version | cut -d. -f1)

if [ "$major" -ge 18 ]; then
    echo -e "${GREEN}✓${NC} Node.js v$node_version (>= 18 required)"
else
    echo -e "${RED}✗${NC} Node.js v$node_version (>= 18 required)"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Checking Ollama service..."
echo "-------------------------"
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama service is running"
    
    # Check for llama3.2:3b model
    if ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
        echo -e "${GREEN}✓${NC} Llama 3.2 3B model is available"
    else
        echo -e "${YELLOW}⚠${NC}  Llama 3.2 3B model not found"
        echo "    Run: ollama pull llama3.2:3b"
    fi
else
    echo -e "${RED}✗${NC} Ollama service is not running"
    echo "    Run: ollama serve"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Checking project structure..."
echo "----------------------------"
check_dir "backend"
check_dir "frontend"
check_dir "data"
check_dir "logs"

echo ""
echo "Checking backend files..."
echo "------------------------"
check_file "backend/main.py"
check_file "backend/config.py"
check_file "backend/models.py"
check_dir "backend/agents"
check_dir "backend/services"
check_dir "backend/security"

echo ""
echo "Checking frontend files..."
echo "-------------------------"
check_file "frontend/package.json"
check_file "frontend/vite.config.js"
check_file "frontend/index.html"
check_dir "frontend/src"

echo ""
echo "Checking configuration..."
echo "------------------------"
check_file ".env"
check_file "requirements.txt"

echo ""
echo "Checking Python virtual environment..."
echo "-------------------------------------"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Python virtual environment exists"
    
    if [ -f "venv/bin/activate" ]; then
        echo -e "${GREEN}✓${NC} Virtual environment is properly set up"
    else
        echo -e "${RED}✗${NC} Virtual environment is incomplete"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC}  Virtual environment not found"
    echo "    Run: python3 -m venv venv"
fi

echo ""
echo "Checking Python dependencies..."
echo "------------------------------"
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null
    
    if python -c "import fastapi" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} FastAPI is installed"
    else
        echo -e "${YELLOW}⚠${NC}  FastAPI not found"
        echo "    Run: pip install -r requirements.txt"
    fi
    
    if python -c "import chromadb" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ChromaDB is installed"
    else
        echo -e "${YELLOW}⚠${NC}  ChromaDB not found"
        echo "    Run: pip install -r requirements.txt"
    fi
    
    deactivate 2>/dev/null
fi

echo ""
echo "Checking frontend dependencies..."
echo "--------------------------------"
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓${NC} Frontend dependencies are installed"
else
    echo -e "${YELLOW}⚠${NC}  Frontend dependencies not found"
    echo "    Run: cd frontend && npm install"
fi

echo ""
echo "=========================================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! You're ready to start.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Make sure Ollama is running: ollama serve"
    echo "  2. Start the application: ./start.sh"
    echo "  3. Open http://localhost:3000"
else
    echo -e "${RED}✗ Found $ERRORS issue(s). Please fix them before starting.${NC}"
    echo ""
    echo "To fix issues, try running: ./setup.sh"
fi
echo "=========================================================="
