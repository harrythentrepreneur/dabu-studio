#!/bin/bash

# RunPod Setup Script
# This script helps set up RunPod integration from scratch

set -e

echo "🚀 RunPod Setup Assistant"
echo "========================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local response
    
    read -p "$prompt [$default]: " response
    echo "${response:-$default}"
}

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is installed and running"

# Step 2: Check for .env file
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp deployment/.env.example "$ENV_FILE"
    echo "✅ Created .env file from template"
fi

# Step 3: Configure RunPod credentials
echo ""
echo "🔑 RunPod Configuration"
echo "----------------------"
echo "Please provide your RunPod credentials."
echo "Get them from: https://www.runpod.io/console/user/settings"
echo ""

# Check if credentials already exist
if grep -q "RUNPOD_API_KEY=" "$ENV_FILE" 2>/dev/null; then
    EXISTING_KEY=$(grep "RUNPOD_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    if [ ! -z "$EXISTING_KEY" ] && [ "$EXISTING_KEY" != "your-runpod-api-key-here" ]; then
        echo "✅ RunPod API key already configured"
    else
        RUNPOD_API_KEY=$(prompt_with_default "RunPod API Key" "")
        if [ ! -z "$RUNPOD_API_KEY" ]; then
            sed -i.bak "s/RUNPOD_API_KEY=.*/RUNPOD_API_KEY=$RUNPOD_API_KEY/" "$ENV_FILE"
            echo "✅ RunPod API key saved"
        fi
    fi
else
    # Add RunPod configuration to .env
    echo "" >> "$ENV_FILE"
    echo "# RunPod Configuration" >> "$ENV_FILE"
    
    RUNPOD_API_KEY=$(prompt_with_default "RunPod API Key" "")
    echo "RUNPOD_API_KEY=$RUNPOD_API_KEY" >> "$ENV_FILE"
    
    echo "RUNPOD_ENDPOINT_ID=" >> "$ENV_FILE"
    echo "RUNPOD_BASE_URL=https://api.runpod.ai/v2" >> "$ENV_FILE"
    echo "RUNPOD_TIMEOUT=600" >> "$ENV_FILE"
    echo "RUNPOD_POLL_INTERVAL=2" >> "$ENV_FILE"
    
    echo "✅ RunPod configuration added to .env"
fi

# Step 4: Docker Hub configuration
echo ""
echo "🐳 Docker Hub Configuration"
echo "--------------------------"
echo "A Docker Hub account is required to push the worker image."
echo "Sign up free at: https://hub.docker.com/signup"
echo ""

DOCKER_USERNAME=$(prompt_with_default "Docker Hub Username" "$USER")

# Step 5: Build decision
echo ""
echo "📦 Build Options"
echo "----------------"
echo "1. Build and deploy now"
echo "2. Set up only (build later)"
echo ""
BUILD_CHOICE=$(prompt_with_default "Choose option (1 or 2)" "2")

if [ "$BUILD_CHOICE" = "1" ]; then
    echo ""
    echo "🔨 Building Docker image..."
    export DOCKER_USERNAME="$DOCKER_USERNAME"
    cd deployment
    ./deploy.sh
    cd ..
    
    echo ""
    echo "✅ Docker image built and pushed!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Go to RunPod Console: https://www.runpod.io/console/serverless"
    echo "2. Click 'New Endpoint'"
    echo "3. Configure with:"
    echo "   - Container Image: $DOCKER_USERNAME/tiktok-video-processor:latest"
    echo "   - Container Disk: 20 GB"
    echo "   - GPU Type: T4 (recommended for cost)"
    echo "   - Max Workers: 3"
    echo "   - Idle Timeout: 5 seconds"
    echo "   - Enable FlashBoot: Yes"
    echo "4. Copy the Endpoint ID"
    echo "5. Run: ./update-endpoint.sh <endpoint-id>"
else
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "📋 To deploy later, run:"
    echo "   cd deployment"
    echo "   DOCKER_USERNAME=$DOCKER_USERNAME ./deploy.sh"
fi

echo ""
echo "📚 Documentation"
echo "---------------"
echo "- Quick Start: runpod/README.md"
echo "- Deployment Guide: runpod/docs/DEPLOYMENT_GUIDE.md"
echo "- RunPod Docs: https://docs.runpod.io"
echo ""
echo "🎉 RunPod setup complete!"