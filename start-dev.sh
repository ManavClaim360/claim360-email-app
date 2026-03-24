#!/usr/bin/env bash
# start-dev.sh — Start both backend and frontend for local development
# Usage: bash start-dev.sh

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        Claim360 — Dev Server        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check backend .env
if [ ! -f backend/.env ]; then
  echo "⚠️  backend/.env not found — copying from .env.example"
  cp backend/.env.example backend/.env
  echo "   → Edit backend/.env before starting."
  exit 1
fi

# Check frontend .env
if [ ! -f frontend/.env ]; then
  cp frontend/.env.example frontend/.env
fi

# Install frontend deps if needed
if [ ! -d frontend/node_modules ]; then
  echo "📦 Installing frontend dependencies..."
  cd frontend && npm install && cd ..
fi

# Start backend in background
echo "🚀 Starting FastAPI backend on http://localhost:8000 ..."
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend
echo "🌐 Starting React frontend on http://localhost:3000 ..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers running:"
echo "   Frontend → http://localhost:3000"
echo "   Backend  → http://localhost:8000"
echo "   API Docs → http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
