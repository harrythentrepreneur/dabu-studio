#!/bin/bash

# RunPod Deployment Script
# Builds and pushes Docker image to RunPod

set -e

echo "🚀 RunPod Worker Deployment Script"
echo "=================================="

# Configuration
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-docker-username"}
IMAGE_NAME="tiktok-video-processor"
IMAGE_TAG=${IMAGE_TAG:-"latest"}
FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if logged into Docker Hub
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "📝 Please log in to Docker Hub:"
    docker login
fi

echo "📦 Building RunPod worker Docker image..."
cd runpod_worker

# Build the image
docker build -t $FULL_IMAGE .

echo "📤 Pushing image to Docker Hub..."
docker push $FULL_IMAGE

echo "✅ Image pushed successfully: $FULL_IMAGE"
echo ""
echo "📋 Next steps:"
echo "1. Go to RunPod dashboard: https://www.runpod.io/console/serverless"
echo "2. Create a new serverless endpoint"
echo "3. Use this Docker image: $FULL_IMAGE"
echo "4. Configure environment variables:"
echo "   - GEMINI_API_KEY"
echo "   - DO_SPACES_KEY (optional)"
echo "   - DO_SPACES_SECRET (optional)"
echo "5. Copy the endpoint ID to your .env file as RUNPOD_ENDPOINT_ID"
echo ""
echo "🎉 Deployment preparation complete!"