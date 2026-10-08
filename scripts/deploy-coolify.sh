#!/bin/bash

# Coolify Deployment Script
# Builds and prepares containers for Coolify deployment

set -e  # Exit on any error

echo "🚀 Coolify Deployment Script"
echo "=============================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.template to .env and configure your settings"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "✅ Environment loaded"
echo "   Mode: ${ENVIRONMENT_MODE:-HYBRID}"
echo "   Frontend URL: ${NEXT_PUBLIC_API_URL:-http://localhost:5000}"

# Build frontend for Coolify
echo ""
echo "🔨 Building Frontend..."
cd frontend
docker build \
    --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" \
    --build-arg NEXT_PUBLIC_BACKEND_URL="${NEXT_PUBLIC_BACKEND_URL}" \
    --build-arg NEXT_PUBLIC_CLOUD="${NEXT_PUBLIC_CLOUD}" \
    -t dabu-frontend:coolify \
    .

if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    exit 1
fi

cd ..

# Build backend API for Coolify
echo ""
echo "🔨 Building Backend API..."
cd backend
docker build \
    -f Dockerfile.coolify \
    -t dabu-backend:coolify \
    .

if [ $? -eq 0 ]; then
    echo "✅ Backend API build successful"
else
    echo "❌ Backend API build failed"
    exit 1
fi

cd ..

echo ""
echo "🎉 Coolify Deployment Ready!"
echo "=============================="
echo "Images built:"
echo "  • dabu-frontend:coolify"
echo "  • dabu-backend:coolify"
echo ""
echo "Next steps for Coolify:"
echo "1. Push images to your container registry"
echo "2. Create two services in Coolify:"
echo "   - Frontend: dabu-frontend:coolify (port 3000)"
echo "   - Backend: dabu-backend:coolify (port 5000)"
echo "3. Set environment variables in Coolify"
echo "4. Deploy!"
echo ""
echo "Environment variables to set in Coolify:"
echo "  • GEMINI_API_KEY"
echo "  • DO_SPACES_KEY, DO_SPACES_SECRET, DO_SPACES_BUCKET"
echo "  • RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID"
echo "  • ENVIRONMENT_MODE=HYBRID"