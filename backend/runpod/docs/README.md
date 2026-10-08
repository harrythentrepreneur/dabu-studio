# RunPod Deployment Guide for CapCut Web Automation

This guide covers deploying the CapCut Web automation service to RunPod's serverless infrastructure.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Deployment Process](#deployment-process)
5. [Testing the Deployment](#testing-the-deployment)
6. [Using the API](#using-the-api)
7. [Monitoring and Scaling](#monitoring-and-scaling)
8. [Troubleshooting](#troubleshooting)
9. [Cost Optimization](#cost-optimization)

## Overview

The CapCut Web automation service has been redesigned to use browser-based automation with Playwright instead of local PyAutoGUI. This enables:

- **Scalability**: Process multiple videos concurrently
- **Reliability**: No screen lock or UI issues
- **Cloud-Native**: Runs on any Linux server
- **Cost-Effective**: 70-80% cheaper than Windows servers

### Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Flask API   │────▶│  RunPod         │
│   (Next.js)     │     │  (Backend)   │     │  Serverless     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │ CapCut Web     │
                                              │ (Browser)      │
                                              └────────────────┘
```

## Prerequisites

### Required Accounts
1. **RunPod Account**: Sign up at [runpod.io](https://www.runpod.io/)
2. **Docker Hub Account**: For storing Docker images
3. **Cloud Storage**: Digital Ocean Spaces or AWS S3

### Required Tools
- Docker Desktop installed locally
- Python 3.9+ with pip
- Git
- RunPod CLI (will be installed automatically)

### API Keys Needed
- RunPod API Key
- Docker Hub credentials
- Cloud storage credentials (DO Spaces or S3)

## Environment Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd backend
```

### 2. Create Environment Variables
Create a `.env.production` file:

```bash
# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key_here

# Docker Registry
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
DOCKER_IMAGE=capcut-web-automation

# Cloud Storage (Digital Ocean Spaces)
STORAGE_PROVIDER=digitalocean
DO_SPACES_KEY=your_spaces_key
DO_SPACES_SECRET=your_spaces_secret
DO_SPACES_BUCKET=your-bucket
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_REGION=nyc3

# Or AWS S3
# STORAGE_PROVIDER=s3
# AWS_ACCESS_KEY_ID=your_aws_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret
# S3_BUCKET=tiktok-video-automation
# AWS_REGION=us-east-1

# Service Configuration
MAX_WORKERS=10
USE_ORCHESTRATOR=true
ENABLE_MONITORING=true
DEBUG_SCREENSHOTS=false
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-runpod.txt
playwright install chromium
```

## Deployment Process

### Option 1: Automated Deployment Script

```bash
# Make script executable
chmod +x scripts/deploy_runpod.sh

# Load environment variables
source .env.production

# Run deployment
./scripts/deploy_runpod.sh
```

The script will:
1. Build the Docker image
2. Push to Docker registry
3. Create RunPod template
4. Deploy serverless endpoint
5. Test the deployment

### Option 2: Manual Deployment

#### Step 1: Build Docker Image
```bash
docker build -f Dockerfile.runpod -t capcut-web-automation:latest .
```

#### Step 2: Tag and Push to Registry
```bash
docker tag capcut-web-automation:latest your-username/capcut-web-automation:latest
docker push your-username/capcut-web-automation:latest
```

#### Step 3: Create RunPod Template

Go to [RunPod Console](https://console.runpod.io/serverless/user/templates) and create a new template:

- **Name**: CapCut Web Automation
- **Container Image**: `your-username/capcut-web-automation:latest`
- **Container Disk**: 20 GB
- **Min Workers**: 0
- **Max Workers**: 20
- **GPU Type**: AMPERE_16 (or CPU if no GPU needed)
- **Idle Timeout**: 60 seconds
- **Scaler Type**: Queue Delay
- **Scaler Value**: 4

#### Step 4: Create Serverless Endpoint

```python
import runpod

runpod.api_key = "your_api_key"

endpoint = runpod.create_serverless_endpoint(
    name="CapCut Web Automation",
    template_id="your_template_id",
    gpu_type="AMPERE_16",
    min_workers=0,
    max_workers=20
)

print(f"Endpoint ID: {endpoint['id']}")
print(f"Endpoint URL: https://api.runpod.ai/v2/{endpoint['id']}/runsync")
```

## Testing the Deployment

### 1. Health Check
```python
import runpod
import json

runpod.api_key = "your_api_key"

result = runpod.run_sync(
    endpoint_id="your_endpoint_id",
    input_payload={"type": "health_check"}
)

print(json.dumps(result, indent=2))
```

Expected response:
```json
{
  "output": {
    "status": "healthy",
    "timestamp": "2025-01-15T10:00:00.000Z",
    "stats": {
      "queue": {"queued": 0, "processing": 0, "completed": 0},
      "workers": {"max": 10, "active": 1}
    }
  }
}
```

### 2. Process Test Video
```python
import runpod
import base64

# Read video file
with open("test_video.mp4", "rb") as f:
    video_base64 = base64.b64encode(f.read()).decode()

result = runpod.run_sync(
    endpoint_id="your_endpoint_id",
    input_payload={
        "type": "process_video",
        "video_base64": video_base64,
        "caption_style": "TikTok Bold",
        "request_id": "test_001"
    }
)

print(f"Success: {result['output']['success']}")
if result['output']['success']:
    print(f"Result URL: {result['output']['result']['captioned_video_url']}")
```

## Using the API

### API Endpoint Format
```
https://api.runpod.ai/v2/{endpoint_id}/runsync  # Synchronous
https://api.runpod.ai/v2/{endpoint_id}/run      # Asynchronous
```

### Request Format

#### Process Video with URL
```json
{
  "input": {
    "type": "process_video",
    "video_url": "https://example.com/video.mp4",
    "caption_style": "TikTok Bold",
    "request_id": "req_123",
    "timeout": 300
  }
}
```

#### Process Video with Base64
```json
{
  "input": {
    "type": "process_video",
    "video_base64": "base64_encoded_video_data",
    "caption_style": "TikTok Pop",
    "request_id": "req_124"
  }
}
```

#### Get Request Status
```json
{
  "input": {
    "type": "get_status",
    "request_id": "req_123"
  }
}
```

#### Get Statistics
```json
{
  "input": {
    "type": "get_stats"
  }
}
```

### Caption Styles Available
- TikTok Bold
- TikTok Pop
- TikTok Glow
- TikTok Classic
- TikTok Neon
- TikTok Shadow
- TikTok Outline
- TikTok Gradient
- TikTok Minimal

### Response Format

#### Success Response
```json
{
  "output": {
    "success": true,
    "request_id": "req_123",
    "result": {
      "captioned_video_path": "/tmp/output.mp4",
      "captioned_video_url": "https://storage.example.com/output.mp4",
      "caption_style": "TikTok Bold",
      "processing_time": 45.2
    }
  },
  "status": "COMPLETED"
}
```

#### Error Response
```json
{
  "output": {
    "success": false,
    "error": "Failed to process video: Browser timeout",
    "traceback": "..."
  },
  "status": "FAILED"
}
```

## Monitoring and Scaling

### RunPod Dashboard
Monitor your endpoint at: `https://console.runpod.io/serverless/user/endpoints`

Key metrics to watch:
- **Request Queue Length**
- **Active Workers**
- **Average Processing Time**
- **Error Rate**
- **Cost per Request**

### Auto-Scaling Configuration

Edit scaling in RunPod console:
- **Min Workers**: 0 (scale to zero when idle)
- **Max Workers**: 20-50 (based on budget)
- **Idle Timeout**: 60-120 seconds
- **Scaler Type**: Queue Delay
- **Scaler Value**: 4 (workers per 4 queued requests)

### Custom Monitoring

```python
# Get detailed stats
result = runpod.run_sync(
    endpoint_id="your_endpoint_id",
    input_payload={"type": "get_stats"}
)

stats = result['output']['stats']
print(f"Queue: {stats['queue']}")
print(f"Workers: {stats['workers']}")
print(f"Resources: {stats['resources']}")
```

## Troubleshooting

### Common Issues

#### 1. Browser Timeout
**Problem**: Browser automation times out
**Solution**: 
- Increase timeout in environment variables
- Check CapCut Web is accessible
- Verify network connectivity

#### 2. Out of Memory
**Problem**: Container runs out of memory
**Solution**:
- Reduce MAX_WORKERS
- Increase container resources
- Optimize browser settings

#### 3. Storage Errors
**Problem**: Can't upload/download files
**Solution**:
- Verify storage credentials
- Check bucket permissions
- Ensure sufficient storage space

#### 4. Cold Start Delays
**Problem**: First request takes too long
**Solution**:
- Keep minimum workers at 1
- Use FlashBoot if available
- Optimize Docker image size

### Debug Mode

Enable debug mode for detailed logs:

```bash
# In .env
DEBUG_SCREENSHOTS=true
RUNPOD_DEBUG_LEVEL=DEBUG
```

### Logs

Access logs via RunPod CLI:
```bash
runpod logs <endpoint_id> --tail 100
```

Or via API:
```python
logs = runpod.get_logs(endpoint_id="your_endpoint_id", limit=100)
for log in logs:
    print(log)
```

## Cost Optimization

### Tips for Reducing Costs

1. **Use CPU-only instances** if GPU not needed
   - 80% cheaper than GPU instances
   - Sufficient for browser automation

2. **Optimize Worker Configuration**
   ```python
   # Efficient settings
   min_workers=0  # Scale to zero
   max_workers=10  # Limit max cost
   idle_timeout=60  # Quick shutdown
   ```

3. **Use Spot Instances**
   - 50-70% cheaper than on-demand
   - Good for non-critical workloads

4. **Implement Request Batching**
   - Process multiple videos per worker
   - Reduces cold start overhead

5. **Cache Common Resources**
   - Store frequently used files in container
   - Reduces download time and bandwidth

### Cost Calculation

```
Cost = (Active Time × Instance Rate) + (Storage × Storage Rate)

Example:
- Instance: $0.00055/second (CPU)
- Processing: 60 seconds/video
- Videos/day: 100
- Daily cost: 100 × 60 × $0.00055 = $3.30/day
```

## Advanced Configuration

### Custom Browser Settings

Edit `capcut_web_service.py`:
```python
browser_args = [
    '--disable-gpu',  # Save resources
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-web-security',  # For cross-origin
    '--window-size=1920,1080'
]
```

### Parallel Processing

Enable orchestrator for concurrent processing:
```bash
USE_ORCHESTRATOR=true
MAX_WORKERS=10
```

### Regional Deployment

Deploy to multiple regions for lower latency:
```python
regions = ['US-WEST', 'EU-CENTRAL', 'ASIA-PACIFIC']
for region in regions:
    endpoint = runpod.create_serverless_endpoint(
        name=f"CapCut-{region}",
        region=region,
        # ... other config
    )
```

## Security Best Practices

1. **Use Secrets Management**
   ```bash
   runpod secret create STORAGE_KEY "your_secret_value"
   ```

2. **Implement Rate Limiting**
   ```python
   # In handler
   if request_count > MAX_REQUESTS_PER_MINUTE:
       return {"error": "Rate limit exceeded"}
   ```

3. **Validate Inputs**
   ```python
   # Validate video size
   if video_size > MAX_VIDEO_SIZE:
       return {"error": "Video too large"}
   ```

4. **Use Signed URLs**
   - Generate temporary URLs for uploads/downloads
   - Expire after short period

5. **Monitor for Abuse**
   - Track usage per user
   - Alert on suspicious patterns

## Support and Resources

- **RunPod Documentation**: https://docs.runpod.io/
- **RunPod Discord**: https://discord.gg/runpod
- **GitHub Issues**: Report bugs in the repository
- **CapCut Web**: https://www.capcut.com/

## Next Steps

1. Test with sample videos
2. Set up monitoring dashboards
3. Configure alerts for errors
4. Optimize for your specific use case
5. Scale based on demand

---

*Last updated: January 2025*