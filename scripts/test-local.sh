#!/bin/bash

# Local Testing Script
# Simulates the full Coolify + RunPod architecture locally

set -e  # Exit on any error

echo "🧪 Local Testing Script"
echo "======================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from template..."
    cp .env.template .env
    echo "❗ Please edit .env with your API keys before running again"
    exit 1
fi

echo "✅ Docker is running"
echo "✅ Environment file found"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Validate required environment variables
missing_vars=()

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    missing_vars+=("GEMINI_API_KEY")
fi

if [ -z "$DO_SPACES_KEY" ] || [ "$DO_SPACES_KEY" = "your_do_spaces_key_here" ]; then
    missing_vars+=("DO_SPACES_KEY")
fi

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf "   • %s\n" "${missing_vars[@]}"
    echo "Please update your .env file"
    exit 1
fi

echo "✅ Required environment variables set"

# Start the local environment
echo ""
echo "🚀 Starting Local Environment..."
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml build
docker-compose -f docker-compose.local.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking Service Health..."

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend (http://localhost:3000) - Ready"
else
    echo "❌ Frontend (http://localhost:3000) - Not responding"
fi

# Check backend API
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Backend API (http://localhost:5000) - Ready"
else
    echo "❌ Backend API (http://localhost:5000) - Not responding"
fi

# Check RunPod worker
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ RunPod Worker (http://localhost:8000) - Ready"
else
    echo "❌ RunPod Worker (http://localhost:8000) - Not responding"
fi

echo ""
echo "🎉 Local Environment Running!"
echo "============================="
echo "Services:"
echo "  • Frontend:     http://localhost:3000"
echo "  • Backend API:  http://localhost:5000"
echo "  • RunPod Worker: http://localhost:8000"
echo ""
echo "Test the application:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Go to Express Builder"
echo "3. Upload videos and enter a script"
echo "4. Test processing (will use local RunPod worker)"
echo ""
echo "Logs:"
echo "  docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo "Stop:"
echo "  docker-compose -f docker-compose.local.yml down"