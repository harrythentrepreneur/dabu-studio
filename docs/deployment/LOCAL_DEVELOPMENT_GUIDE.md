# 🏠 Local Development Guide

This guide provides step-by-step instructions for running the TikTok Video Ad Automation app locally using Docker.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git (to clone the repository)
- 8GB+ RAM recommended

### 1. Environment Setup

Copy the environment template and configure:
```bash
cp .env.template .env
# Edit .env with your actual API keys or use the test values for local development
```

### 2. Start the Application

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Check that services are running
docker-compose -f docker-compose.local.yml ps
```

### 3. Access the Application

- **Frontend (Main Interface)**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **Health Check**: http://localhost:5001/api/health

## 🏗️ Architecture Overview

### Local Service Configuration

| Service | Port | Container Port | Status | Description |
|---------|------|----------------|--------|-------------|
| Frontend | 3000 | 3000 | ✅ Required | Next.js UI (Express Builder, etc.) |
| Backend API | 5001 | 5000 | ✅ Required | Flask API server |
| RunPod Worker | 8000 | 8000 | ⚠️ Optional | Heavy processing (may restart) |

### Current Working Status

- ✅ **Frontend**: Fully functional with all UI components
- ✅ **Backend API**: Core endpoints working, CapCut features disabled (requires Playwright)
- ⚠️ **RunPod Worker**: Available but restarting (not needed for basic UI testing)

## 🧪 Testing the Application

### Available Features

1. **Express Builder** - Main video creation interface
2. **Quick Create** - Simplified video generation
3. **GIF Studio** - GIF moment analysis  
4. **Clip Studio** - Video clip extraction
5. **Trending Audio** - Audio management
6. **Dashboard** - Overview and analytics

### Basic Test Flow

1. **Open Browser**: Navigate to http://localhost:3000
2. **Upload Videos**: Add source video files (MP4 recommended)
3. **Add Script**: Enter your 15-45 second script text
4. **Configure Settings**: Adjust duration and processing options
5. **Start Processing**: Click create and monitor progress
6. **Download Results**: Get generated video, script, and timestamps

### API Testing

Test the backend directly:
```bash
# Health check
curl http://localhost:5001/api/health

# Generate request ID
curl -X POST http://localhost:5001/api/generate-request-id

# Check system status
curl http://localhost:5001/api/status
```

## 🛠️ Management Commands

### Service Management

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Stop all services
docker-compose -f docker-compose.local.yml down

# Restart specific service
docker-compose -f docker-compose.local.yml restart backend-api

# View service status
docker-compose -f docker-compose.local.yml ps
```

### Logs and Debugging

```bash
# View logs for all services
docker-compose -f docker-compose.local.yml logs

# View logs for specific service
docker-compose -f docker-compose.local.yml logs frontend
docker-compose -f docker-compose.local.yml logs backend-api

# Follow logs in real-time
docker-compose -f docker-compose.local.yml logs -f backend-api
```

### Rebuilding Services

```bash
# Rebuild specific service (after code changes)
docker-compose -f docker-compose.local.yml build frontend
docker-compose -f docker-compose.local.yml restart frontend

# Force rebuild without cache
docker-compose -f docker-compose.local.yml build --no-cache backend-api

# Rebuild and restart in one command
docker-compose -f docker-compose.local.yml up -d --build
```

## 🔧 Configuration Details

### Environment Variables

Key variables in `.env` file:

```bash
# API Configuration
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# Storage Configuration  
DO_SPACES_KEY=your_spaces_key
DO_SPACES_SECRET=your_spaces_secret
DO_SPACES_BUCKET=your-bucket

# Local URLs
NEXT_PUBLIC_API_URL=http://localhost:5001
NEXT_PUBLIC_BACKEND_URL=http://localhost:5001
```

### Port Configuration

The application uses the following port mapping:

- Frontend: `3000:3000` (direct mapping)
- Backend: `5001:5000` (mapped to avoid conflicts)
- RunPod Worker: `8000:8000` (direct mapping)

## ⚡ Performance Notes

### Resource Usage

- **Frontend**: ~200MB RAM, minimal CPU
- **Backend API**: ~500MB RAM, low CPU (no heavy processing)
- **RunPod Worker**: ~1GB+ RAM, high CPU (when processing)

### Processing Modes

The local setup runs in **HYBRID mode**:
- Light operations processed by backend-api
- Heavy operations would route to RunPod worker (simulated locally)
- File storage uses Digital Ocean Spaces

## 🔍 Troubleshooting

### Common Issues

#### Port 5000 Already in Use
```bash
# Kill process using port 5000
lsof -ti:5000 | xargs kill -9

# Or change backend port in docker-compose.local.yml
```

#### Backend Service Restarting
```bash
# Check logs for errors
docker-compose -f docker-compose.local.yml logs backend-api

# Rebuild and restart
docker-compose -f docker-compose.local.yml build backend-api
docker-compose -f docker-compose.local.yml restart backend-api
```

#### Frontend Build Errors
```bash
# Rebuild frontend
docker-compose -f docker-compose.local.yml build frontend
docker-compose -f docker-compose.local.yml restart frontend
```

### Cleanup Commands

```bash
# Stop and remove all containers
docker-compose -f docker-compose.local.yml down

# Remove containers and volumes
docker-compose -f docker-compose.local.yml down -v

# Remove unused images
docker system prune -f
```

## 🚀 Next Steps

Once you have the app running locally:

1. **Test Core Features**: Try uploading videos and creating scripts
2. **API Integration**: Test the REST endpoints with your preferred tools
3. **Development**: Make code changes and rebuild services as needed
4. **Production**: Use the deployment guides for Coolify + RunPod setup

## 📞 Support

- **Documentation**: Check `CLAUDE.md` for technical details
- **Deployment**: See `README_DEPLOYMENT.md` for production setup
- **Issues**: The frontend and backend logs provide detailed error information

---

**Status**: ✅ Fully Functional Local Environment  
**Last Updated**: August 18, 2025  
**Tested Components**: Frontend ✅ | Backend API ✅ | Docker Setup ✅