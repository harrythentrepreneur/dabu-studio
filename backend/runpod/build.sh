#!/bin/bash

# RunPod Docker Build Script
# Builds and optionally pushes the Docker image for RunPod deployment

set -e

# Configuration
IMAGE_NAME="tiktok-express-builder"
TAG="${1:-latest}"
REGISTRY="${DOCKER_REGISTRY:-}"  # Optional: your Docker registry URL

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Building RunPod Docker Image${NC}"
echo "Image: ${IMAGE_NAME}:${TAG}"

# Check if we're in the right directory
if [ ! -f "runpod/Dockerfile" ]; then
    echo -e "${RED}Error: Must run from backend directory${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -f runpod/Dockerfile -t ${IMAGE_NAME}:${TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker build successful!${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Tag for registry if specified
if [ ! -z "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${TAG}"
    echo -e "${YELLOW}Tagging image for registry: ${FULL_IMAGE_NAME}${NC}"
    docker tag ${IMAGE_NAME}:${TAG} ${FULL_IMAGE_NAME}
    
    # Ask if we should push
    read -p "Push to registry? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Pushing to registry...${NC}"
        docker push ${FULL_IMAGE_NAME}
        echo -e "${GREEN}✅ Push complete!${NC}"
    fi
fi

# Display image info
echo -e "${GREEN}📦 Image Details:${NC}"
docker images ${IMAGE_NAME}:${TAG}

echo -e "${GREEN}🎉 Build complete!${NC}"
echo ""
echo "To run locally for testing:"
echo "  docker run -it --rm ${IMAGE_NAME}:${TAG} /bin/bash"
echo ""
echo "To deploy to RunPod:"
echo "  1. Push image to a registry (Docker Hub, GitHub Container Registry, etc.)"
echo "  2. Use the image URL in RunPod serverless configuration"