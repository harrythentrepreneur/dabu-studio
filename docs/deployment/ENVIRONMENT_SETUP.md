# Environment Variables Setup Guide

This guide explains how to configure environment variables for DABU deployment on Coolify (frontend) and RunPod (backend).

## 🚀 Frontend Deployment (Coolify)

### 1. Create Environment File

```bash
cd frontend
cp env.example .env.production
```

### 2. Configure Digital Ocean Spaces

```bash
# Get these from your Digital Ocean account
DO_SPACES_KEY=your_actual_access_key
DO_SPACES_SECRET=your_actual_secret_key
DO_SPACES_BUCKET=your-bucket
DO_SPACES_ENDPOINT=https://sfo3.digitaloceanspaces.com
DO_SPACES_REGION=sfo3
```

### 3. Configure RunPod Integration

```bash
# Get these from your RunPod account
RUNPOD_API_KEY=your_actual_runpod_api_key
RUNPOD_ENDPOINT_ID=your_actual_endpoint_id
```

### 4. Set in Coolify

- Go to your Coolify project
- Navigate to Environment Variables
- Add each variable from `.env.production`

## 🔧 Backend Deployment (RunPod)

### 1. Local Development

```bash
cd dabu-backend
cp env.example .env
# Edit .env with your actual values
```

### 2. RunPod Environment Variables

In your RunPod endpoint configuration, set these environment variables:

#### Required Variables:

```bash
# Digital Ocean Spaces
DO_SPACES_KEY=your_actual_access_key
DO_SPACES_SECRET=your_actual_secret_key
DO_SPACES_BUCKET=your-bucket
DO_SPACES_ENDPOINT=https://sfo3.digitaloceanspaces.com
DO_SPACES_REGION=sfo3

# AI Services
GEMINI_API_KEY=your_actual_gemini_api_key

# Processing Configuration
MAX_WORKERS=5
MAX_QUEUE_SIZE=1000
DEBUG_MODE=false
```

#### Optional Variables:

```bash
# OpenAI (for voiceover analysis)
OPENAI_API_KEY=your_openai_api_key

# CapCut Automation
CAPCUT_WINDOWS_IP=192.168.1.100
CAPCUT_API_KEY=your_capcut_api_key

# Logging
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

## 🔑 How to Get API Keys

### Digital Ocean Spaces

1. Go to [Digital Ocean](https://cloud.digitalocean.com/)
2. Navigate to Spaces
3. Create a new Space or use existing
4. Go to API → Spaces Keys
5. Generate new key pair

### RunPod

1. Go to [RunPod](https://runpod.io/)
2. Navigate to API Keys
3. Generate new API key
4. Note your endpoint ID from the endpoint you created

### Google Gemini

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Enable Gemini API in Google Cloud Console

## 🚨 Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use different keys** for development/staging/production
3. **Rotate API keys** regularly
4. **Limit permissions** - only grant necessary access
5. **Monitor usage** - set up alerts for unusual activity

## 🔍 Verification

### Frontend Health Check

```bash
curl https://your-domain.com/api/process
# Should return environment status
```

### Backend Health Check

```bash
curl https://your-runpod-endpoint.runpod.net/health
# Should return health status
```

## 🆘 Troubleshooting

### Common Issues:

1. **"DO_SPACES_KEY not found"**

   - Check if environment variable is set in Coolify
   - Verify the variable name matches exactly

2. **"RunPod endpoint unreachable"**

   - Verify RUNPOD_ENDPOINT_ID is correct
   - Check if RunPod endpoint is running
   - Verify RUNPOD_API_KEY has correct permissions

3. **"Upload failed"**

   - Check DO_SPACES credentials
   - Verify bucket exists and is accessible
   - Check CORS configuration on DO Spaces

4. **"Processing failed"**
   - Check backend logs in RunPod
   - Verify all required environment variables are set
   - Check if AI API keys are valid

## 📝 Environment Variable Reference

| Variable             | Frontend | Backend | Required | Description                |
| -------------------- | -------- | ------- | -------- | -------------------------- |
| `DO_SPACES_KEY`      | ✅       | ✅      | Yes      | Digital Ocean access key   |
| `DO_SPACES_SECRET`   | ✅       | ✅      | Yes      | Digital Ocean secret key   |
| `DO_SPACES_BUCKET`   | ✅       | ✅      | Yes      | Storage bucket name        |
| `DO_SPACES_ENDPOINT` | ✅       | ✅      | Yes      | DO Spaces endpoint URL     |
| `DO_SPACES_REGION`   | ✅       | ✅      | Yes      | DO Spaces region           |
| `RUNPOD_API_KEY`     | ✅       | ❌      | Yes      | RunPod API authentication  |
| `RUNPOD_ENDPOINT_ID` | ✅       | ❌      | Yes      | RunPod endpoint identifier |
| `GEMINI_API_KEY`     | ❌       | ✅      | Yes      | Google Gemini AI API key   |
| `MAX_WORKERS`        | ❌       | ✅      | No       | Max concurrent workers     |
| `DEBUG_MODE`         | ❌       | ✅      | No       | Enable debug logging       |

## 🎯 Next Steps

1. ✅ Set up environment variables
2. ✅ Deploy frontend to Coolify
3. ✅ Deploy backend to RunPod
4. ✅ Test video upload and processing
5. ✅ Monitor logs and performance
6. ✅ Set up monitoring and alerts
