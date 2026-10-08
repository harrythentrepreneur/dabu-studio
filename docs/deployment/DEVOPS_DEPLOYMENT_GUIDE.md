# 🔧 DevOps Deployment Guide
## TikTok Video Ad Automation Platform

**For DevOps/Infrastructure Teams**

---

## 📋 Executive Summary

**Application**: TikTok Video Ad Automation Platform  
**Architecture**: Hybrid Cloud (Coolify + RunPod)  
**Tech Stack**: Next.js Frontend, Python Flask API, Playwright Browser Automation  
**Deployment Model**: Microservices with intelligent workload routing  

### Key Characteristics:
- **Compute-Intensive**: Video processing, AI analysis, browser automation
- **File-Heavy**: Large video uploads (up to 2GB per request)
- **API-Driven**: RESTful API with Server-Sent Events for real-time status
- **Hybrid Processing**: Light tasks local, heavy tasks cloud

---

## 🏗️ Infrastructure Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Client   │────│   Coolify        │────│   RunPod        │
│   (Browser)     │    │   (Light Tasks)  │    │   (Heavy Tasks) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              │                          │
                       ┌──────────────┐         ┌───────────────┐
                       │  Next.js     │         │  Python +     │
                       │  Frontend    │         │  Playwright   │
                       │              │         │  + FFmpeg     │
                       │  Flask API   │         │  + Gemini AI  │
                       │  (Routing)   │         │               │
                       └──────────────┘         └───────────────┘
                              │                          │
                              └────────────────────────────────────┐
                                                                   │
                                                    ┌─────────────────┐
                                                    │ Digital Ocean   │
                                                    │ Spaces          │
                                                    │ (File Storage)  │
                                                    └─────────────────┘
```

---

## 🛠️ Deployment Components

### 1. Frontend (Coolify)
**Service**: `dabu-frontend`  
**Technology**: Next.js 15.4.6 (React 19.1.0)  
**Container**: `dabu-frontend:coolify`  
**Port**: `3000`  
**Resources**: 
- CPU: 1-2 cores
- RAM: 1-2GB
- Storage: 1GB

### 2. Backend API (Coolify)
**Service**: `dabu-backend-api`  
**Technology**: Python 3.11 + Flask  
**Container**: `dabu-backend:coolify`  
**Port**: `5000`  
**Resources**:
- CPU: 2-4 cores  
- RAM: 2-4GB
- Storage: 5GB
- **Function**: API routing, light processing only

### 3. RunPod Worker (RunPod Serverless)
**Service**: `dabu-video-processor`  
**Technology**: Python 3.11 + Playwright + FFmpeg  
**Container**: `dabu-runpod-worker:latest`  
**Port**: `8000`  
**Resources**:
- CPU: 8+ cores (recommended)
- RAM: 16GB+ (recommended)  
- GPU: Optional (RTX 4090 for AI acceleration)
- Storage: 20GB+ container disk
- **Function**: Heavy video processing, browser automation

---

## 🔧 Environment Configuration

### Core Environment Variables

| Variable | Required | Component | Description |
|----------|----------|-----------|-------------|
| `ENVIRONMENT_MODE` | Yes | Backend | `HYBRID` for Coolify, `PRODUCTION` for RunPod |
| `GEMINI_API_KEY` | Yes | Both | Google Gemini AI API key |
| `DO_SPACES_KEY` | Yes | Both | Digital Ocean Spaces access key |
| `DO_SPACES_SECRET` | Yes | Both | Digital Ocean Spaces secret key |
| `DO_SPACES_BUCKET` | Yes | Both | Bucket name (no default) |
| `RUNPOD_API_KEY` | Yes | Backend | RunPod API key for job routing |
| `RUNPOD_ENDPOINT_ID` | Yes | Backend | RunPod endpoint ID for heavy processing |

### Frontend Environment Variables (Coolify)

```bash
# Build-time variables
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_BACKEND_URL=https://api.yourdomain.com  
NEXT_PUBLIC_CLOUD=true

# Runtime variables
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

### Backend Environment Variables (Coolify)

```bash
# Deployment mode
ENVIRONMENT_MODE=HYBRID
FLASK_ENV=production

# API Keys
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key_optional

# Digital Ocean Spaces
DO_SPACES_KEY=your_do_key
DO_SPACES_SECRET=your_do_secret
DO_SPACES_BUCKET=your-bucket
DO_SPACES_REGION=sfo3
DO_SPACES_ENDPOINT=https://sfo3.digitaloceanspaces.com

# RunPod Integration
RUNPOD_API_KEY=your_runpod_key
RUNPOD_ENDPOINT_ID=your_runpod_endpoint

# Local processing (disable in production)
USE_LOCAL_DOCKER=false
```

### RunPod Environment Variables

```bash
# Processing mode
ENVIRONMENT_MODE=PRODUCTION

# API Keys (same as backend)
GEMINI_API_KEY=your_gemini_key
DO_SPACES_KEY=your_do_key
DO_SPACES_SECRET=your_do_secret
DO_SPACES_BUCKET=your-bucket

# Browser automation settings
MAX_BROWSER_INSTANCES=3
ENABLE_MONITORING=true
DEBUG_SCREENSHOTS=true
DISPLAY=:99
```

---

## 🚀 Deployment Process

### Phase 1: Infrastructure Preparation

1. **Set up Coolify instance**
   - Minimum: 4 CPU cores, 8GB RAM, 50GB storage
   - Recommended: 8 CPU cores, 16GB RAM, 100GB storage

2. **Set up RunPod account**
   - Create serverless endpoint
   - Configure container registry access

3. **Set up Digital Ocean Spaces**
   - Create bucket (e.g., `dabu`)
   - Configure CORS for web uploads
   - Set lifecycle policies for cleanup

### Phase 2: Container Registry

Push built images to your container registry:

```bash
# Build images
docker build -f frontend/Dockerfile -t your-registry/dabu-frontend:coolify ./frontend
docker build -f backend/Dockerfile.coolify -t your-registry/dabu-backend:coolify ./backend  
docker build -f backend/Dockerfile.runpod -t your-registry/dabu-runpod:latest ./backend

# Push to registry
docker push your-registry/dabu-frontend:coolify
docker push your-registry/dabu-backend:coolify
docker push your-registry/dabu-runpod:latest
```

### Phase 3: Coolify Deployment

1. **Create Frontend Service**
   - Source: Docker Image
   - Image: `your-registry/dabu-frontend:coolify`
   - Port: 3000
   - Domain: Configure your frontend domain
   - Environment: Set frontend variables

2. **Create Backend Service**
   - Source: Docker Image  
   - Image: `your-registry/dabu-backend:coolify`
   - Port: 5000
   - Domain: Configure your API domain
   - Environment: Set backend variables

3. **Configure Load Balancer/Proxy**
   - Frontend: `https://app.yourdomain.com`
   - Backend: `https://api.yourdomain.com`

### Phase 4: RunPod Deployment

1. **Create Serverless Endpoint**
   - Image: `your-registry/dabu-runpod:latest`
   - Container Port: 8000
   - Container Disk: 20GB+
   - Environment: Set RunPod variables

2. **Configure Scaling**
   - Min Workers: 0 (cost optimization)
   - Max Workers: 5-10 (based on expected load)
   - Idle Timeout: 30 seconds

3. **Get Endpoint ID**
   - Note the generated endpoint ID
   - Update Coolify backend with `RUNPOD_ENDPOINT_ID`

---

## 🔍 Health Checks & Monitoring

### Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Frontend | `GET /api/health` | `200 OK` |
| Backend | `GET /api/health` | `200 OK` with service status |
| RunPod | `GET /health` | `200 OK` |

### Monitoring Metrics

**Frontend (Coolify)**:
- Response time < 200ms
- Error rate < 1%
- Memory usage < 1GB

**Backend (Coolify)**:
- Response time < 500ms  
- CPU usage < 70%
- Memory usage < 2GB
- API request success rate > 99%

**RunPod Worker**:
- Processing time per job
- Success rate > 95%
- Resource utilization
- Cost per execution

### Log Aggregation

**Coolify Logs**:
```bash
# Frontend logs
docker logs coolify-frontend

# Backend logs  
docker logs coolify-backend
```

**RunPod Logs**:
- Available in RunPod console
- Configure log forwarding if needed

---

## 🛡️ Security Configuration

### Network Security
- All services use HTTPS/TLS
- Internal communication over private networks where possible
- API rate limiting enabled

### Container Security
- Non-root users in all containers
- Read-only root filesystems where possible
- Security context constraints applied

### API Security
- CORS configured for frontend domain only
- Request size limits (2GB max for video uploads)
- API key validation on all external requests

### Secrets Management
- Environment variables injected at runtime
- No secrets in container images
- Secrets rotation capability

---

## 💰 Cost Optimization

### Coolify (Fixed Costs)
- Right-size instances based on actual usage
- Enable horizontal pod autoscaling
- Use reserved instances if applicable

### RunPod (Pay-per-Use)
- **Current Model**: Serverless (pay per second)
- **Cost Factors**: CPU time, GPU time, storage
- **Optimization**: 
  - Minimize processing time
  - Use appropriate instance types
  - Set aggressive idle timeouts

### Digital Ocean Spaces
- **Storage**: ~$5/month per 250GB
- **Bandwidth**: $0.01/GB outbound
- **Optimization**: Set lifecycle rules to delete old files

### Expected Monthly Costs (Estimate)
- **Coolify**: $50-200/month (depending on instance size)
- **RunPod**: $0.10-2.00 per video processed
- **Digital Ocean Spaces**: $20-100/month (depending on usage)
- **APIs**: Gemini AI ~$0.50 per video

---

## 🚨 Disaster Recovery

### Backup Strategy
- **Code**: Git repository (already handled)
- **Configuration**: Environment variables documented
- **Data**: User uploads auto-deleted after processing
- **State**: Stateless application (no persistent data)

### Recovery Procedures
1. **Frontend Down**: Redeploy Coolify frontend service
2. **Backend Down**: Redeploy Coolify backend service  
3. **RunPod Down**: Workers auto-scale, check RunPod console
4. **Storage Down**: Temporary service degradation, no data loss

### Rollback Strategy
- **Container Images**: Tagged with build numbers
- **Environment**: Configuration versioned in Git
- **Database**: N/A (stateless)

---

## 🔧 Troubleshooting Guide

### Common Issues

**"Frontend not loading"**
- Check Coolify frontend service status
- Verify `NEXT_PUBLIC_API_URL` points to correct backend
- Check domain configuration and SSL certificates

**"API requests failing"**  
- Check Coolify backend service logs
- Verify environment variables are set
- Test backend health endpoint

**"Video processing stuck"**
- Check RunPod endpoint status in console
- Verify `RUNPOD_ENDPOINT_ID` is correct
- Check Digital Ocean Spaces connectivity

**"Upload failures"**
- Check file size limits (2GB max)
- Verify Digital Ocean Spaces CORS configuration
- Check available storage space

### Debug Commands

```bash
# Check service status
curl -f https://api.yourdomain.com/api/health

# Get environment configuration  
curl https://api.yourdomain.com/api/environment

# Check processing status
curl https://api.yourdomain.com/api/status/request_id

# View real-time logs
docker logs -f service_name
```

---

## 📞 Support & Escalation

### Tier 1: Application Issues
- Frontend not responding
- API errors  
- Processing failures
- **Contact**: Development team

### Tier 2: Infrastructure Issues
- Coolify service failures
- RunPod connectivity issues
- Digital Ocean Spaces problems
- **Contact**: DevOps team

### Tier 3: Vendor Issues
- RunPod platform problems
- Digital Ocean outages  
- Gemini AI API issues
- **Contact**: Vendor support + DevOps

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] All environment variables documented and secured
- [ ] Container images built and pushed to registry
- [ ] Digital Ocean Spaces bucket created and configured
- [ ] RunPod account set up with payment method
- [ ] SSL certificates configured for domains

### Coolify Deployment
- [ ] Frontend service deployed and accessible
- [ ] Backend service deployed and responding to health checks
- [ ] Environment variables configured correctly
- [ ] Domains configured with proper SSL
- [ ] Load balancer configured if needed

### RunPod Deployment  
- [ ] Serverless endpoint created with correct image
- [ ] Environment variables set in RunPod console
- [ ] Scaling configuration set appropriately
- [ ] Endpoint ID updated in Coolify backend

### Post-Deployment
- [ ] End-to-end testing completed
- [ ] Monitoring and alerting configured
- [ ] Cost tracking enabled
- [ ] Documentation updated with actual endpoints/domains
- [ ] Team trained on monitoring and troubleshooting

---

**Questions?** Contact the development team with this document for technical clarification.

**Estimated Deployment Time**: 4-8 hours for experienced DevOps team

**Complexity**: Medium (hybrid cloud architecture with multiple moving parts)