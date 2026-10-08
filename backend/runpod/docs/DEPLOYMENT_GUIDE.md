# RunPod Deployment Guide

## Architecture Overview

This setup creates a lightweight Flask backend that delegates heavy video processing to RunPod serverless workers:

```
[Frontend Apps] → [Flask AsPI (Lightweight)] → [RunPod Workers (Heavy Processing)]
                           ↓
                    [Redis (SSE/Cache)]
```

## Components

### 1. Lihtweight Flask Backend (`Dockerfile.lightweight`)
- Minimal dependencies (no FFmpeg, no heavy ML libraries)
- Handles API requests and orchestration
- Delegates heavy processing to RunPod
- Can run on cheap hosting (Railway, Render, etc.)

### 2. RunPod Worker (`runpod_worker/`)
- Full video processing capabilities
- FFmpeg with GPU acceleration
- Gemini API integration
- Runs only when needed (serverless)

## Deployment Steps

### Step 1: Set Up RunPod Worker

1. **Create RunPod Account**
   - Sign up at [runpod.io](https://www.runpod.io)
   - Add credits to your account

2. **Build and Push Worker Image**
   ```bash
   cd backend
   
   # Set your Docker Hub username
   export DOCKER_USERNAME="your-username"
   
   # Run deployment script
   ./deploy-runpod.sh
   ```

3. **Create Serverless Endpoint**
   - Go to [RunPod Console](https://www.runpod.io/console/serverless)
   - Click "New Endpoint"
   - Configure:
     - Name: `tiktok-video-processor`
     - Container Image: `your-username/tiktok-video-processor:latest`
     - Container Disk: 20 GB
     - Volume Disk: 0 GB (unless needed)
     - GPU Type: Choose based on needs (T4 for cost-effective)
     - Active Workers: 0 (scales to 0 when idle)
     - Max Workers: 3-5 (based on expected load)
     - Idle Timeout: 5 seconds
     - Execution Timeout: 600 seconds
     - FlashBoot: Enable for faster cold starts

4. **Set Environment Variables in RunPod**
   - Click on your endpoint
   - Go to "Environment Variables"
   - Add:
     ```
     GEMINI_API_KEY=your-key
     DO_SPACES_KEY=your-key (optional)
     DO_SPACES_SECRET=your-secret (optional)
     ```

5. **Copy Endpoint ID**
   - Find your endpoint ID in the RunPod dashboard
   - Add to your `.env` file as `RUNPOD_ENDPOINT_ID`

### Step 2: Deploy Flask Backend

1. **Configure Environment**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Local Deployment (Docker)**
   ```bash
   ./deploy-flask.sh
   ```

3. **Production Deployment Options**

   **Option A: Railway**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Deploy
   railway login
   railway init
   railway up
   ```

   **Option B: Render**
   - Connect GitHub repo
   - Use `Dockerfile.lightweight`
   - Set environment variables in dashboard

   **Option C: DigitalOcean App Platform**
   ```bash
   doctl apps create --spec app.yaml
   ```

   **Option D: AWS ECS/Fargate**
   - Use provided `Dockerfile.lightweight`
   - Create task definition with environment variables
   - Deploy to Fargate for serverless containers

### Step 3: Update Frontend

1. **Update API endpoints**
   ```javascript
   // In your frontend .env
   NEXT_PUBLIC_API_URL=https://your-flask-backend.com
   ```

2. **Use RunPod endpoints**
   ```javascript
   // For heavy processing
   fetch(`${API_URL}/api/process/runpod`, {
     method: 'POST',
     body: JSON.stringify({
       script: '...',
       videos: ['...'],
       duration: 30
     })
   })
   ```

## API Endpoints

### Main Processing (via RunPod)
```
POST /api/process/runpod
```

### Task-Specific Endpoints
```
POST /api/runpod/merge      # Merge videos
POST /api/runpod/compress   # Compress video
POST /api/runpod/extract    # Extract segments
POST /api/runpod/voiceover  # Add voiceover
```

### Status & Management
```
GET  /api/runpod/status/:job_id
POST /api/runpod/cancel/:job_id
GET  /api/runpod/health
GET  /api/runpod/config
```

## Cost Optimization

### RunPod Pricing (as of 2024)
- **Serverless**: Pay per second of GPU usage
- **T4 GPU**: ~$0.00011/second ($0.40/hour)
- **RTX 3090**: ~$0.00044/second ($1.58/hour)
- **No charges when idle** (scales to 0)

### Example Costs
- 100 videos/day × 30 seconds processing = $0.33/day (T4)
- 1000 videos/day × 30 seconds = $3.30/day (T4)

### Tips for Cost Reduction
1. **Use FlashBoot** - 2-second cold starts
2. **Set aggressive idle timeout** - 5 seconds
3. **Use smallest suitable GPU** - T4 for most tasks
4. **Batch processing** - Process multiple videos per job
5. **Cache results** - Use Redis/S3 for repeated content

## Monitoring

### RunPod Dashboard
- Real-time metrics
- Request logs
- Error tracking
- Cost monitoring

### Flask Backend
```bash
# View logs
docker logs -f flask-api

# Monitor health
curl http://localhost:5000/api/health

# Check RunPod connection
curl http://localhost:5000/api/runpod/health
```

## Troubleshooting

### Common Issues

1. **RunPod endpoint not responding**
   - Check endpoint status in dashboard
   - Verify API key and endpoint ID
   - Check worker logs in RunPod console

2. **Slow cold starts**
   - Enable FlashBoot
   - Keep minimal dependencies in worker
   - Pre-warm endpoint with health checks

3. **High costs**
   - Review GPU selection
   - Optimize processing code
   - Implement caching layer

4. **Connection errors**
   - Check network configuration
   - Verify environment variables
   - Test with RunPod API directly

## Local Development

### Using Docker Compose
```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up flask-api

# View logs
docker-compose logs -f flask-api
```

### Testing RunPod Integration
```bash
# Test health
curl http://localhost:5000/api/runpod/health

# Test processing
curl -X POST http://localhost:5000/api/process/runpod \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Test script",
    "videos": ["url1", "url2"],
    "duration": 30
  }'
```

## Security Considerations

1. **API Keys**
   - Never commit `.env` files
   - Use environment variables in production
   - Rotate keys regularly

2. **File Upload Limits**
   - Set `MAX_FILE_SIZE_MB` in environment
   - Validate file types
   - Scan for malware if needed

3. **Rate Limiting**
   - Implement rate limiting in Flask
   - Use RunPod's built-in limits
   - Monitor for abuse

4. **Network Security**
   - Use HTTPS in production
   - Implement CORS properly
   - Validate all inputs

## Scaling Considerations

### Horizontal Scaling
- Flask backend can run multiple instances
- RunPod auto-scales workers
- Use load balancer for Flask instances

### Vertical Scaling
- Upgrade RunPod GPU type
- Increase worker memory/disk
- Optimize video processing algorithms

### Caching Strategy
- Cache processed videos in S3
- Use Redis for session data
- Implement CDN for static assets

## Support

- RunPod Documentation: [docs.runpod.io](https://docs.runpod.io)
- RunPod Discord: [discord.gg/runpod](https://discord.gg/runpod)
- GitHub Issues: [Your repo issues]