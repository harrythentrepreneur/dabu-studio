#!/bin/bash

# Docker run script for production
# Usage: ./scripts/run-docker.sh [tag]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TAG=${1:-latest}
IMAGE_NAME="tiktok-frontend"
CONTAINER_NAME="tiktok-frontend-app"
PORT=${PORT:-3000}

echo -e "${YELLOW}Starting Docker container: ${CONTAINER_NAME}${NC}"

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}Error: .env.production not found!${NC}"
    echo -e "${YELLOW}Please create .env.production from .env.production.example${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
fi

# Run the container
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:3000 \
  -e NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" \
  -e NEXT_PUBLIC_BACKEND_URL="${NEXT_PUBLIC_BACKEND_URL}" \
  -e NEXT_PUBLIC_CLOUD="${NEXT_PUBLIC_CLOUD}" \
  --restart unless-stopped \
  ${IMAGE_NAME}:${TAG}

echo -e "${GREEN}✓ Container started successfully${NC}"
echo -e "${YELLOW}Container name: ${CONTAINER_NAME}${NC}"
echo -e "${YELLOW}Access the app at: http://localhost:${PORT}${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  View logs:    docker logs -f ${CONTAINER_NAME}"
echo -e "  Stop:         docker stop ${CONTAINER_NAME}"
echo -e "  Start:        docker start ${CONTAINER_NAME}"
echo -e "  Remove:       docker rm -f ${CONTAINER_NAME}"