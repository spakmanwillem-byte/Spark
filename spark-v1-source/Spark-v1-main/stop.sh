#!/bin/bash
#
# Spark Core 4.1 - Stop Script (Linux/Odroid)
# Stop backend + frontend services
#

echo "================================================================"
echo "🛑 Spark Core 4.1 - Shutdown"
echo "================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Check if supervisor is available
if command -v supervisorctl &> /dev/null; then
    echo "Stopping services via supervisor..."
    sudo supervisorctl stop backend frontend
    echo -e "${GREEN}✅ Services stopped${NC}"
else
    echo "Stopping services manually..."
    
    # Stop backend
    if [ -f "$BACKEND_DIR/backend.pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo -e "${GREEN}✅ Backend stopped (PID: $BACKEND_PID)${NC}"
        fi
        rm -f "$BACKEND_DIR/backend.pid"
    fi
    
    # Stop frontend
    if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo -e "${GREEN}✅ Frontend stopped (PID: $FRONTEND_PID)${NC}"
        fi
        rm -f "$FRONTEND_DIR/frontend.pid"
    fi
    
    # Kill any remaining processes on ports
    echo "Cleaning up ports..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Ports cleaned${NC}"
fi

echo ""
echo "================================================================"
echo "✅ Shutdown complete"
echo "================================================================"
