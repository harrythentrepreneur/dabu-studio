#!/bin/bash

# Docker build script for production
# Usage: ./scripts/build-docker.sh [tag]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TAG=${1:-latest}
IMAGE_NAME="tiktok-frontend"

echo -e "${YELLOW}Building Docker image: ${IMAGE_NAME}:${TAG}${NC}"

# Check if .env file exists
if [ ! -f .env.production ]; then
    echo -e "${RED}Warning: .env.production not found!${NC}"
    echo -e "${YELLOW}Using example values from .env.production.example${NC}"
    cp .env.production.example .env.production
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Build the Docker image
docker build \
  --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" \
  --build-arg NEXT_PUBLIC_BACKEND_URL="${NEXT_PUBLIC_BACKEND_URL}" \
  --build-arg NEXT_PUBLIC_CLOUD="${NEXT_PUBLIC_CLOUD}" \
  -t ${IMAGE_NAME}:${TAG} \
  -t ${IMAGE_NAME}:latest \
  .

echo -e "${GREEN}✓ Docker image built successfully: ${IMAGE_NAME}:${TAG}${NC}"
echo -e "${YELLOW}To run the container:${NC}"
echo -e "docker run -d -p 3000:3000 --name tiktok-frontend ${IMAGE_NAME}:${TAG}"