# RunPod Integration & Environment Configuration

This directory contains all RunPod-related code for serverless GPU video processing with support for LOCAL, HYBRID, and PRODUCTION environment modes.

## Directory Structure

```
runpod/
├── client/           # Flask backend client for RunPod API
│   ├── __init__.py
│   └── client.py     # RunPodClient class
│
├── worker/           # RunPod serverless worker code
│   ├── handler.py    # Original handler for video processing
│   ├── main_handler.py # Main RunPod entry point
│   ├── gemini_processor.py # Gemini API integration
│   ├── Dockerfile    # Worker container definition
│   └── requirements.txt # Worker dependencies
│
├── deployment/       # Deployment scripts and configs
│   ├── Dockerfile    # Production Docker image
│   ├── deploy.sh     # Deployment script
│   ├── requirements.txt # RunPod-specific requirements
│   └── .env.example  # Environment variables template
│
└── docs/            # Documentation
    ├── README.md    # Quick start guide
    └── DEPLOYMENT_GUIDE.md # Detailed deployment instructions
```

## Quick Start

### 1. Prerequisites
- Docker installed and running
- RunPod account with API key
- Docker Hub account

### 2. Configuration
```bash
# Copy environment template
cp deployment/.env.example ../.env

# Edit .env with your credentials
RUNPOD_API_KEY=your-api-key
RUNPOD_ENDPOINT_ID=your-endpoint-id
```

### 3. Deploy Worker
```bash
cd deployment
./deploy.sh
```

### 4. Test Integration
```bash
# From backend directory
python -c "from runpod.client import RunPodClient; client = RunPodClient(); print(client.health_check())"
```

## Components

### Client (`/client`)
Python client for Flask backend to communicate with RunPod workers.

**Key Features:**
- Async/sync job submission
- Status polling
- Health checks
- Error handling

### Worker (`/worker`)
Serverless worker that runs on RunPod infrastructure.

**Capabilities:**
- Video processing with FFmpeg
- Gemini API integration
- CapCut automation
- Cloud storage support

### Deployment (`/deployment`)
Scripts and configurations for building and deploying to RunPod.

**Includes:**
- Multi-stage Dockerfile for optimized images
- Deployment automation script
- Environment configuration templates

## Usage Examples

### From Flask Backend
```python
from runpod.client import RunPodClient, RunPodProcessor

# Initialize client
client = RunPodClient()

# Process video
processor = RunPodProcessor(client)
result = processor.process_video_pipeline(
    request_id="req_123",
    script="Your script here",
    video_urls=["url1", "url2"],
    target_duration=30
)
```

### Direct API Call
```bash
curl -X POST http://localhost:5000/api/process/runpod \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Test script",
    "videos": ["url1", "url2"],
    "duration": 30
  }'
```

## Monitoring

### Check Worker Status
```bash
# Health check
curl http://localhost:5000/api/runpod/health

# Get stats
curl http://localhost:5000/api/runpod/stats
```

### View Logs
- RunPod Dashboard: [runpod.io/console](https://runpod.io/console)
- Local logs: `backend/logs/runpod_*.log`

## Cost Optimization

- **Use T4 GPUs** for most tasks ($0.40/hour)
- **Enable FlashBoot** for 2-second cold starts
- **Set aggressive idle timeout** (5 seconds)
- **Implement caching** for repeated content

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # macOS
   open -a Docker
   ```

2. **Missing credentials**
   - Check `.env` file has RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID

3. **Build fails**
   - Ensure Docker Hub login: `docker login`
   - Check disk space: `docker system df`

4. **Worker timeouts**
   - Increase timeout in client configuration
   - Check RunPod dashboard for errors

## Support

- RunPod Docs: [docs.runpod.io](https://docs.runpod.io)
- RunPod Discord: [discord.gg/runpod](https://discord.gg/runpod)
- Project Issues: [GitHub Issues](https://github.com/your-repo/issues)