#!/bin/bash

# Script to update RunPod endpoint ID in .env file

if [ $# -eq 0 ]; then
    echo "Usage: ./update-endpoint.sh <endpoint-id>"
    echo ""
    echo "Get your endpoint ID from: https://www.runpod.io/console/serverless"
    exit 1
fi

ENDPOINT_ID=$1
ENV_FILE="../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found. Run ./setup.sh first."
    exit 1
fi

# Update or add RUNPOD_ENDPOINT_ID
if grep -q "RUNPOD_ENDPOINT_ID=" "$ENV_FILE"; then
    sed -i.bak "s/RUNPOD_ENDPOINT_ID=.*/RUNPOD_ENDPOINT_ID=$ENDPOINT_ID/" "$ENV_FILE"
else
    echo "RUNPOD_ENDPOINT_ID=$ENDPOINT_ID" >> "$ENV_FILE"
fi

echo "✅ Updated RUNPOD_ENDPOINT_ID to: $ENDPOINT_ID"
echo ""
echo "You can now test the connection with:"
echo "  python -m runpod.test"