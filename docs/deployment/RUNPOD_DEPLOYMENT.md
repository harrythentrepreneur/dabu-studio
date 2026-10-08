# RunPod Deployment Guide

This guide walks you through deploying the backend processing to RunPod serverless infrastructure.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│   Next.js    │────▶│   RunPod    │
│             │     │  (Coolify)   │     │ (Serverless)│
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────┐
│         Digital Ocean Spaces (Storage)          │
└─────────────────────────────────────────────────┘
```

## Prerequisites

1. RunPod account with API access
2. Docker Hub or GitHub Container Registry account
3. Digital Ocean Spaces bucket configured
4. Gemini API key

## Step 1: Build and Push Docker Image

### Option A: Using Docker Hub

```bash
# Build the RunPod-optimized image
cd backend
docker build -f Dockerfile.runpod -t yourusername/dabu-runpod:latest .

# Push to Docker Hub
docker login
docker push yourusername/dabu-runpod:latest
```

### Option B: Using GitHub Container Registry

```bash
# Build and tag for GitHub
docker build -f backend/Dockerfile.runpod -t ghcr.io/yourusername/dabu-runpod:latest backend/

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push the image
docker push ghcr.io/yourusername/dabu-runpod:latest
```

## Step 2: Create RunPod Serverless Endpoint

1. Go to [RunPod Console](https://www.runpod.io/console/serverless)
2. Click "Create Endpoint"
3. Configure the endpoint:

   ```
   Name: dabu-express-builder
   Container Image: yourusername/dabu-runpod:latest
   Container Port: 8000
   Container Disk: 20 GB
   GPU Type: None (CPU only) or T4 (if needed)
   Min Workers: 0
   Max Workers: 5
   Idle Timeout: 60 seconds
   ```

4. Set Environment Variables:

   ```
   GEMINI_API_KEY=your-gemini-api-key
   DO_SPACES_KEY=your-spaces-key
   DO_SPACES_SECRET=your-spaces-secret
   DO_SPACES_BUCKET=your-bucket
   DO_SPACES_REGION=sfo3
   DO_SPACES_ENDPOINT=https://sfo3.digitaloceanspaces.com
   ENVIRONMENT_MODE=PRODUCTION
   MAX_WORKERS=3
   DEBUG_MODE=false
   ```

5. Click "Create" and note your Endpoint ID

## Step 3: Configure Digital Ocean Spaces CORS

1. Go to your DO Spaces bucket settings
2. Add CORS configuration:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration>
    <CORSRule>
        <AllowedOrigin>https://your-app-domain.com</AllowedOrigin>
        <AllowedOrigin>http://localhost:3000</AllowedOrigin>
        <AllowedMethod>GET</AllowedMethod>
        <AllowedMethod>PUT</AllowedMethod>
        <AllowedMethod>POST</AllowedMethod>
        <AllowedMethod>DELETE</AllowedMethod>
        <AllowedHeader>*</AllowedHeader>
        <MaxAgeSeconds>3000</MaxAgeSeconds>
    </CORSRule>
</CORSConfiguration>
```

Or using the DO Spaces UI:
- Origins: `https://your-app-domain.com, http://localhost:3000`
- Methods: `GET, PUT, POST, DELETE`
- Headers: `*`
- Max Age: `3000`

## Step 4: Update Next.js Environment

1. Copy the example environment file:
   ```bash
   cp frontend/.env.example frontend/.env.local
   ```

2. Update with your values:
   ```env
   # RunPod Configuration
   RUNPOD_API_KEY=your-runpod-api-key
   RUNPOD_ENDPOINT_ID=your-endpoint-id-from-step-2
   
   # Digital Ocean Spaces
   DO_SPACES_KEY=your-spaces-key
   DO_SPACES_SECRET=your-spaces-secret
   DO_SPACES_BUCKET=your-bucket
   DO_SPACES_REGION=sfo3
   DO_SPACES_ENDPOINT=https://sfo3.digitaloceanspaces.com
   
   # Gemini API
   GEMINI_API_KEY=your-gemini-api-key
   ```

## Step 5: Deploy Next.js to Coolify

1. Push your code to GitHub
2. In Coolify, create a new service:
   - Type: Next.js
   - Repository: Your GitHub repo
   - Branch: main or deploy
   - Root Directory: /frontend
   - Build Command: `pnpm install && pnpm build`
   - Start Command: `pnpm start`

3. Set environment variables in Coolify (same as .env.local)

4. Deploy!

## Step 6: Test the Deployment

### Test RunPod Health Check
```bash
curl -X GET https://YOUR_ENDPOINT_ID.runpod.net/health \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY"
```

### Test End-to-End Flow
1. Open your deployed Next.js app
2. Go to Express Builder
3. Upload a small test video
4. Add a simple script
5. Click "Build Video"
6. Monitor the progress

## Monitoring and Debugging

### RunPod Logs
- Access via RunPod Console → Your Endpoint → Logs
- Filter by request ID for specific jobs

### Check Job Status
```bash
curl -X GET https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/JOB_ID \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY"
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Upload fails | Check DO Spaces CORS configuration |
| Job stuck in queue | Check RunPod endpoint is active and has available workers |
| Processing fails | Check Gemini API key and quota |
| Results not accessible | Ensure DO Spaces files have public-read ACL |
| Timeout errors | Increase RunPod timeout or optimize video compression |

## Cost Optimization

1. **RunPod Settings:**
   - Set Min Workers to 0 for scale-to-zero
   - Use CPU-only for Express Builder (no GPU needed)
   - Set appropriate idle timeout (60-120 seconds)

2. **Digital Ocean Spaces:**
   - Enable CDN for frequently accessed files
   - Set lifecycle rules to delete old temp files
   - Use Spaces CDN endpoint for serving results

3. **Monitoring Usage:**
   - RunPod: Check usage in dashboard
   - DO Spaces: Monitor bandwidth and storage
   - Gemini API: Track token usage

## Scaling Considerations

### For Higher Load:
1. Increase RunPod max workers (up to 10)
2. Enable RunPod GPU for faster processing
3. Use DO Spaces CDN for result delivery
4. Implement Redis for job queue management

### For Cost Savings:
1. Use spot instances on RunPod
2. Compress videos more aggressively
3. Cache Gemini responses
4. Batch process during off-peak hours

## Security Best Practices

1. **API Keys:**
   - Never commit keys to Git
   - Rotate keys regularly
   - Use different keys for dev/prod

2. **File Access:**
   - Use presigned URLs with expiration
   - Validate file types and sizes
   - Scan uploads for malware

3. **Network:**
   - Use HTTPS everywhere
   - Implement rate limiting
   - Add request signing for webhooks

## Rollback Procedure

If deployment fails:
1. Revert to previous Docker image tag in RunPod
2. Restore previous environment variables
3. Clear DO Spaces temp files
4. Check error logs for root cause

## Support and Troubleshooting

- RunPod Documentation: https://docs.runpod.io
- Digital Ocean Spaces: https://docs.digitalocean.com/products/spaces/
- Next.js Deployment: https://nextjs.org/docs/deployment

For specific issues, check:
- `/backend/logs/` for processing errors
- RunPod endpoint logs for container issues
- Browser console for upload errors
- Next.js server logs in Coolify