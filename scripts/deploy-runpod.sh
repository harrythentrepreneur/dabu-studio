#!/bin/bash

# RunPod Deployment Script
# Builds and deploys heavy processing worker to RunPod

set -e  # Exit on any error

echo "⚡ RunPod Deployment Script"
echo "=========================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.template to .env and configure your settings"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "✅ Environment loaded"
echo "   RunPod API Key: ${RUNPOD_API_KEY:0:10}..."
echo "   RunPod Endpoint: ${RUNPOD_ENDPOINT_ID}"

# Build RunPod worker image
echo ""
echo "🔨 Building RunPod Worker..."
cd backend

# Build the heavy processing container
docker build \
    -f Dockerfile.runpod \
    -t dabu-runpod-worker:latest \
    .

if [ $? -eq 0 ]; then
    echo "✅ RunPod worker build successful"
else
    echo "❌ RunPod worker build failed"
    exit 1
fi

cd ..

# Tag for registry push
REGISTRY_TAG="dabu-runpod-worker:$(date +%Y%m%d_%H%M%S)"
docker tag dabu-runpod-worker:latest $REGISTRY_TAG

echo ""
echo "🎉 RunPod Worker Ready!"
echo "======================"
echo "Images built:"
echo "  • dabu-runpod-worker:latest"
echo "  • $REGISTRY_TAG"
echo ""
echo "Next steps for RunPod:"
echo "1. Push image to Docker Hub or your registry:"
echo "   docker push your-registry/dabu-runpod-worker:latest"
echo ""
echo "2. Create RunPod Serverless Endpoint:"
echo "   • Use the pushed image"
echo "   • Set container port: 8000"
echo "   • Set environment variables:"
echo "     - GEMINI_API_KEY"
echo "     - DO_SPACES_KEY, DO_SPACES_SECRET, DO_SPACES_BUCKET"
echo "     - ENVIRONMENT_MODE=PRODUCTION"
echo ""
echo "3. Update your Coolify backend with:"
echo "   RUNPOD_ENDPOINT_ID=<your-new-endpoint-id>"
echo ""
echo "RunPod Configuration:"
echo "  • CPU: 8+ cores recommended"
echo "  • RAM: 16GB+ recommended"
echo "  • GPU: Optional (for AI acceleration)"
echo "  • Container Disk: 20GB+"