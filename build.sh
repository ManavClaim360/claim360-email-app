#!/usr/bin/env bash
# build.sh — Build frontend and embed it into backend for single Vercel deployment
# Usage: bash build.sh

set -e

echo "🔨 Building Claim360 for production..."

# Build React frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
# Output goes to backend/static (configured in vite.config.js)
cd ..

echo "✅ Frontend built → backend/static/"
echo ""
echo "To deploy backend + embedded frontend to Vercel:"
echo "   vercel --prod"
echo ""
echo "Or deploy frontend separately to Vercel:"
echo "   cd frontend && vercel --prod"
