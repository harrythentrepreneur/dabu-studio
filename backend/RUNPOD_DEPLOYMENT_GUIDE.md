# RunPod Deployment Guide

## Overview
This guide covers deploying the Express Builder and Quick Create services to RunPod serverless infrastructure.

## Architecture

```
Frontend (Next.js on Coolify)
    ↓
Digital Ocean Spaces (File Storage)
    ↓
RunPod Serverless (Processing)
    ↓
Digital Ocean Spaces (Results)
    ↓
Frontend (Display Results)
```

## Prerequisites

1. **RunPod Account**
   - Create account at https://runpod.io
   - Add credits/payment method
   - Generate API key

2. **Digital Ocean Spaces**
   - Create a Space for file storage
   - Generate access keys
   - Configure CORS for browser uploads

3. **Docker Hub Account** (optional)
   - For hosting Docker images
   - Or use RunPod's registry

## Environment Variables

Create `.env` file with:

```bash
# RunPod Configuration
RUNPOD_API_KEY=your-runpod-api-key
RUNPOD_ENDPOINT_ID=your-endpoint-id

# Digital Ocean Spaces
DO_SPACES_KEY=your-spaces-key
DO_SPACES_SECRET=your-spaces-secret
DO_SPACES_BUCKET=your-bucket-name
DO_SPACES_REGION=sfo3
DO_SPACES_ENDPOINT=https://sfo3.digitaloceanspaces.com

# Gemini API (for video analysis)
GEMINI_API_KEY=your-gemini-key

# OpenAI (for voiceover analysis)
OPENAI_API_KEY=your-openai-key
```

## Building the Docker Image

### Option 1: Build Locally and Push

```bash
# Build the optimized image
docker build -f Dockerfile.runpod.optimized -t your-username/express-builder:latest .

# Test locally
docker run --env-file .env your-username/express-builder:latest

# Push to Docker Hub
docker push your-username/express-builder:latest
```

### Option 2: Build on RunPod

```bash
# Use RunPod CLI
runpod build -f Dockerfile.runpod.optimized
```

## Creating RunPod Endpoint

### 1. Create Serverless Endpoint

```bash
# Using RunPod CLI
runpod create endpoint \
  --name "Express Builder" \
  --image "your-username/express-builder:latest" \
  --gpu-type "NVIDIA RTX A4000" \
  --min-workers 0 \
  --max-workers 5 \
  --idle-timeout 60 \
  --execution-timeout 600
```

### 2. Configure via Web UI

1. Go to RunPod Console
2. Click "Serverless" → "New Endpoint"
3. Configure:
   - **Name**: Express Builder
   - **Container Image**: your-username/express-builder:latest
   - **GPU Type**: RTX A4000 (or CPU for testing)
   - **Min Workers**: 0 (scales to zero)
   - **Max Workers**: 5 (based on load)
   - **Idle Timeout**: 60s
   - **Execution Timeout**: 600s (10 min max)
   - **Environment Variables**: Add all from .env

## API Integration

### Frontend API Call

```typescript
// /frontend/app/api/process/route.ts
const RUNPOD_API_KEY = process.env.RUNPOD_API_KEY;
const RUNPOD_ENDPOINT_ID = process.env.RUNPOD_ENDPOINT_ID;

const response = await fetch(
  `https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${RUNPOD_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: {
        request_id: requestId,
        task_type: 'express_builder', // or 'quick_create'
        script: scriptText,
        videos: videoUrls, // Array of DO Spaces URLs
        voiceover: voiceoverUrl, // Optional
        duration: 30,
      }
    })
  }
);
```

### Response Format

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "output": {
    "success": true,
    "request_id": "req_123",
    "videoUrl": "https://spaces.url/output.mp4",
    "scriptUrl": "https://spaces.url/script.txt",
    "timestampsUrl": "https://spaces.url/timestamps.json",
    "captionedVideoUrl": "https://spaces.url/captioned.mp4",
    "segments": [...],
    "processing_time": 120.5
  }
}
```

## Testing

### 1. Test Express Builder

```bash
# Test with curl
curl -X POST https://api.runpod.ai/v2/$ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "request_id": "test_001",
      "task_type": "express_builder",
      "script": "This is a test script",
      "videos": ["https://your-space.sfo3.digitaloceanspaces.com/test.mp4"],
      "duration": 30
    }
  }'
```

### 2. Test Quick Create (with CapCut)

```bash
curl -X POST https://api.runpod.ai/v2/$ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "request_id": "test_002",
      "task_type": "quick_create",
      "script": "Test with captions",
      "videos": ["https://your-space.sfo3.digitaloceanspaces.com/test.mp4"],
      "duration": 30
    }
  }'
```

## Monitoring

### RunPod Dashboard
- View active jobs
- Monitor GPU usage
- Check error logs
- Track costs

### Logging
```python
# Logs are available in RunPod dashboard
logger.info("Processing started")
logger.error("Error details")
```

### Metrics to Track
- Average processing time
- Success rate
- GPU utilization
- Cost per request

## Cost Optimization

### 1. Use Appropriate GPU
- **Express Builder Only**: CPU instance ($0.00006/sec)
- **With CapCut**: GPU instance ($0.00044/sec for A4000)

### 2. Configure Auto-scaling
```json
{
  "min_workers": 0,  // Scale to zero
  "max_workers": 5,  // Peak capacity
  "idle_timeout": 60, // Quick scale down
  "target_queue_size": 2 // Workers per queue size
}
```

### 3. Optimize Docker Image
- Use multi-stage builds
- Minimize dependencies
- Cache model downloads

## Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Increase execution timeout
   - Optimize video processing
   - Use smaller chunk sizes

2. **Memory Issues**
   - Use GPU with more VRAM
   - Process videos in chunks
   - Clean up temp files

3. **CapCut Automation Fails**
   - Check browser installation
   - Verify virtual display
   - Review automation logs

### Debug Mode

Add to environment:
```bash
DEBUG_MODE=true
LOG_LEVEL=debug
```

### Health Check

```bash
# Check endpoint status
curl https://api.runpod.ai/v2/$ENDPOINT_ID/health
```

## Production Checklist

- [ ] Docker image optimized and tested
- [ ] Environment variables configured
- [ ] RunPod endpoint created
- [ ] Auto-scaling configured
- [ ] Monitoring setup
- [ ] Error handling tested
- [ ] Frontend integration verified
- [ ] Cost alerts configured
- [ ] Backup endpoint ready
- [ ] Documentation updated

## Support

- RunPod Discord: https://discord.gg/runpod
- RunPod Docs: https://docs.runpod.io
- GitHub Issues: [Your repo]/issues