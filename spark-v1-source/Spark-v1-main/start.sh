#!/bin/bash
#
# Spark Core 4.1 - Start Script (Linux/Odroid)
# One-click startup voor backend + frontend
#

set -e  # Exit on error

echo "================================================================"
echo "🚀 Spark Core 4.1 - Startup"
echo "================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root (script directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Step 1: Check Dependencies
echo "Step 1: Checking dependencies..."
echo "---"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    echo "Install: sudo apt-get install python3 python3-pip"
    exit 1
fi
echo -e "${GREEN}✅ Python3:${NC} $(python3 --version)"

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    echo "Install: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "         sudo apt-get install -y nodejs"
    exit 1
fi
echo -e "${GREEN}✅ Node.js:${NC} $(node --version)"

# Check yarn
if ! command -v yarn &> /dev/null; then
    echo -e "${RED}❌ Yarn not found${NC}"
    echo "Install: npm install -g yarn"
    exit 1
fi
echo -e "${GREEN}✅ Yarn:${NC} $(yarn --version)"

echo ""

# Step 2: Check if ports are available
echo "Step 2: Checking ports..."
echo "---"

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port in use
    else
        return 0  # Port available
    fi
}

# Check backend port (8001)
if ! check_port 8001; then
    echo -e "${YELLOW}⚠️  Port 8001 already in use${NC}"
    echo "Killing existing backend process..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo -e "${GREEN}✅ Port 8001:${NC} Available"

# Check frontend port (3000)
if ! check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 already in use${NC}"
    echo "Killing existing frontend process..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo -e "${GREEN}✅ Port 3000:${NC} Available"

echo ""

# Step 3: Install dependencies if needed
echo "Step 3: Installing dependencies (if needed)..."
echo "---"

# Backend dependencies
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ ! -f "venv/.dependencies_installed" ]; then
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
    touch venv/.dependencies_installed
    echo -e "${GREEN}✅ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Backend dependencies already installed${NC}"
fi

# Frontend dependencies
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    yarn install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

echo ""

# Step 4: Start Backend
echo "Step 4: Starting backend..."
echo "---"

cd "$BACKEND_DIR"
source venv/bin/activate

# Check if supervisor is available
if command -v supervisorctl &> /dev/null; then
    echo "Using supervisor to start backend..."
    sudo supervisorctl start backend
    echo -e "${GREEN}✅ Backend started via supervisor${NC}"
else
    echo "Starting backend with uvicorn..."
    nohup uvicorn server:app --host 0.0.0.0 --port 8001 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    echo "   Log: $BACKEND_DIR/backend.log"
fi

sleep 3

# Check if backend is running
if curl -s http://localhost:8001/api/emotions/current > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Backend may not be ready yet (this is normal)${NC}"
fi

echo ""

# Step 5: Start Frontend
echo "Step 5: Starting frontend..."
echo "---"

cd "$FRONTEND_DIR"

# Check if supervisor is available
if command -v supervisorctl &> /dev/null; then
    echo "Using supervisor to start frontend..."
    sudo supervisorctl start frontend
    echo -e "${GREEN}✅ Frontend started via supervisor${NC}"
else
    echo "Starting frontend with yarn..."
    nohup yarn start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo "   Log: $FRONTEND_DIR/frontend.log"
fi

echo ""
echo "================================================================"
echo "✅ Spark Core 4.1 - Startup Complete!"
echo "================================================================"
echo ""
echo "🌐 Backend:  http://localhost:8001"
echo "🌐 Frontend: http://localhost:3000"
echo ""
echo "📊 Status check:"
if command -v supervisorctl &> /dev/null; then
    echo "   sudo supervisorctl status"
else
    echo "   Backend:  tail -f $BACKEND_DIR/backend.log"
    echo "   Frontend: tail -f $FRONTEND_DIR/frontend.log"
fi
echo ""
echo "🛑 To stop:"
if command -v supervisorctl &> /dev/null; then
    echo "   sudo supervisorctl stop backend frontend"
else
    echo "   ./stop.sh"
fi
echo ""
echo "================================================================"
