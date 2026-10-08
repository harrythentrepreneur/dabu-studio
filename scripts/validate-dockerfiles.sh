#!/bin/bash

# Docker Build Validation Script
# Validates all Dockerfiles and builds them for testing

set -e

echo "🔍 Docker Build Validation"
echo "========================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is running"

# Validate Dockerfile syntax by attempting builds
cd "$(dirname "$0")/.."

echo ""
echo "🔨 Building Frontend (Coolify)..."
if docker build -f frontend/Dockerfile -t dabu-frontend:validation ./frontend --no-cache; then
    echo "✅ Frontend Dockerfile is valid"
    docker images | grep dabu-frontend:validation
else
    echo "❌ Frontend Dockerfile has issues"
    exit 1
fi

echo ""
echo "🔨 Building Backend API (Coolify)..."
if docker build -f backend/Dockerfile.coolify -t dabu-backend:validation ./backend --no-cache; then
    echo "✅ Backend Dockerfile.coolify is valid"
    docker images | grep dabu-backend:validation
else
    echo "❌ Backend Dockerfile.coolify has issues"
    exit 1
fi

echo ""
echo "🔨 Building RunPod Worker..."
if docker build -f backend/Dockerfile.runpod -t dabu-runpod:validation ./backend --no-cache; then
    echo "✅ Backend Dockerfile.runpod is valid"
    docker images | grep dabu-runpod:validation
else
    echo "❌ Backend Dockerfile.runpod has issues"  
    exit 1
fi

echo ""
echo "🎉 All Docker builds successful!"
echo "==============================="
echo "Built images:"
docker images | grep validation

echo ""
echo "🧹 Cleanup validation images? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    docker rmi dabu-frontend:validation dabu-backend:validation dabu-runpod:validation
    echo "✅ Cleanup complete"
fi

echo ""
echo "✅ All Dockerfiles validated successfully!"
echo "Ready for deployment!"