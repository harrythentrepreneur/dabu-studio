#!/bin/bash

# RunPod Deployment Script for Express Builder
set -e

echo "🚀 RunPod Express Builder Deployment"
echo "====================================="

# Configuration - Update these with your Docker Hub username
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-dockerhub-user"}
IMAGE_NAME="dabu-express-builder"
IMAGE_TAG=${IMAGE_TAG:-"latest"}
FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if already logged into Docker Hub
if docker info 2>/dev/null | grep -q "Username"; then
    echo "✅ Already logged into Docker Hub"
else
    echo "📝 Please login to Docker Hub first:"
    echo "   Run: docker login -u $DOCKER_USERNAME"
    echo "   Then run this script again"
    exit 1
fi

echo ""
echo "📦 Building Docker image..."
docker build -f Dockerfile.runpod.express -t $FULL_IMAGE .

echo ""
echo "📤 Pushing image to Docker Hub..."
docker push $FULL_IMAGE

echo ""
echo "✅ Image pushed successfully!"
echo ""
echo "========================================="
echo "📋 NEXT STEPS TO DEPLOY ON RUNPOD:"
echo "========================================="
echo ""
echo "1. Go to RunPod Console:"
echo "   https://www.runpod.io/console/serverless"
echo ""
echo "2. Click 'New Endpoint' and configure:"
echo "   - Name: dabu-express-builder"
echo "   - Select GPU Type: RTX 4090 or A100 (for faster processing)"
echo "   - Container Image: $FULL_IMAGE"
echo "   - Container Disk: 20 GB"
echo "   - Max Workers: 3"
echo "   - Idle Timeout: 5 seconds"
echo "   - Execution Timeout: 300 seconds"
echo ""
echo "3. Add Environment Variables:"
echo "   - GEMINI_API_KEY: (your key)"
echo "   - OPENAI_API_KEY: (your key)"
echo "   - DO_SPACES_KEY: (your key)"
echo "   - DO_SPACES_SECRET: (your secret)"
echo "   - DO_SPACES_BUCKET: your-bucket"
echo "   - DO_SPACES_REGION: sfo3"
echo ""
echo "4. After deployment, copy the Endpoint ID"
echo "   and update your frontend .env:"
echo "   RUNPOD_ENDPOINT_ID=<your-endpoint-id>"
echo ""
echo "5. Test the endpoint using the RunPod test interface"
echo "   or update your frontend to use the RunPod API"
echo ""
echo "🎉 Docker image ready for RunPod deployment!"
echo "==========================================="