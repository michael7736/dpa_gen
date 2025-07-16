#!/bin/bash

echo "Starting DPA Application..."

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "uvicorn src.api.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

# Activate conda environment and start backend
echo "Starting backend server..."
cd /Users/mdwong001/Desktop/code/rag/DPA
source /Users/mdwong001/mambaforge/bin/activate dpa_gen
# OPENAI_API_KEY should be set in your environment or .env file
# export OPENAI_API_KEY=your_api_key_here
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 10

# Check if backend is running
if curl -s http://localhost:8200/api/v1/health > /dev/null 2>&1; then
    echo "Backend started successfully!"
else
    echo "Backend failed to start. Check backend.log for errors."
    exit 1
fi

# Start frontend
echo "Starting frontend server..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 5

# Check if frontend is running
if curl -s -I http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend started successfully!"
else
    echo "Frontend failed to start. Check frontend.log for errors."
    exit 1
fi

echo ""
echo "===========================================" 
echo "DPA Application is running!"
echo "==========================================="
echo "Frontend: http://localhost:8230"
echo "Backend API: http://localhost:8200"
echo "API Docs: http://localhost:8200/docs"
echo ""
echo "Logs:"
echo "  - Backend: backend.log"
echo "  - Frontend: frontend.log"
echo ""
echo "To stop all services, run: pkill -f 'uvicorn|next dev'"
echo "==========================================="

# Keep script running
wait $BACKEND_PID