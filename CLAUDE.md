# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TikTok video ad automation tool that uses Google Gemini API to match ad scripts with video segments. Takes a script (15-45 seconds), multiple video files, finds optimal timestamps for each script line, and outputs a compiled video with hard cuts and optional voiceover.

## Tech Stack

### Frontend (`/frontend`)
- Next.js 15.4.6 with App Router
- React 19.1.0
- shadcn/ui components
- Tailwind CSS
- TypeScript
- Clerk Authentication
- Stripe Payments
- Features: Express Builder, Clip Studio, GIF Studio, Music Library

### Backend (Separate Repository)
**Repository**: ./backend
- Python 3.9+ for RunPod serverless
- Google Gemini API (gemini-2.5-pro for main processing, gemini-2.5-flash-lite for GIF analysis)
- FFmpeg for video processing
- OpenAI Whisper for voiceover analysis
- Digital Ocean Spaces for file storage
- RunPod for serverless GPU/CPU processing

## High-Level Architecture

### Processing Pipeline (10 Steps)
1. **Optional Voiceover Analysis** - Whisper API for exact timing
2. **Load Inputs** - Script and video files
3. **Merge Videos** - Create full-quality and compressed versions
4. **Upload to Gemini** - Compressed video for analysis
5. **AI Analysis** - Match script segments to video timestamps
6. **Duration Validation** - Ensure within ±15s tolerance
7. **Extract Segments** - From full-quality source
8. **Export Outputs** - Video, script, timestamps
9. **Add Voiceover** - Mux audio if provided
10. **Cleanup** - Remove temporary files

### Architecture

**Frontend** handles:
- User interface and interactions
- File uploads to Digital Ocean Spaces
- API calls to RunPod for processing
- Real-time status updates
- Authentication and payments

**Backend** (via RunPod) handles:
- Video processing pipeline
- AI script-to-video matching
- Caption generation (Quick Create)
- File storage operations

## Development Commands

### Frontend Commands
```bash
cd frontend

# Development server
npm run dev  # http://localhost:3000

# Build for production
npm run build

# Run production build
npm run start

# Lint code
npm run lint
```

# Install dependencies
pnpm install

# Run tests
pnpm test

# Lint code
pnpm lint

# Type check
pnpm typecheck
```

### Docker Local Development Commands

```bash
# Start all services (recommended for local testing)
docker-compose -f docker-compose.local.yml up -d

# Check status of all services
docker-compose -f docker-compose.local.yml ps

# View logs for specific service
docker-compose -f docker-compose.local.yml logs frontend
docker-compose -f docker-compose.local.yml logs backend-api

# Rebuild and restart a service
docker-compose -f docker-compose.local.yml build backend-api
docker-compose -f docker-compose.local.yml restart backend-api

# Stop all services
docker-compose -f docker-compose.local.yml down

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5001
# Health Check: http://localhost:5001/api/health
```

### Environment Setup
```bash
# Backend .env file (backend/.env)
GEMINI_API_KEY=your-api-key-here
DO_SPACES_KEY=optional-for-large-files
DO_SPACES_SECRET=optional-for-large-files
DEBUG_MODE=false  # Set to true for debug data collection

# Frontend uses backend API at http://localhost:5001 (local Docker setup)
```

## API Endpoints

```
POST /api/process                    # Main video processing endpoint
GET  /api/health                    # Health check
GET  /api/generate-request-id       # Generate unique request ID
GET  /api/status-stream/<id>        # SSE endpoint for real-time updates
GET  /api/status                    # System status and configuration
GET  /api/status/<id>               # Check specific request status
GET  /api/result/<id>               # Get completed request results
GET  /api/download/<id>/<type>      # Download results (video, script, timestamps, voiceover, debug)
POST /api/validate                   # Validate input without processing
POST /api/gif-studio/analyze        # Analyze script for GIF moments
POST /api/clip-studio/analyze       # Analyze script for video clips
```

## Key Technical Details

### Video Processing Strategy
- **Two-version approach**: Full quality for extraction, compressed for Gemini
- **Compression**: 480p, 1Mbps, 15fps (target <100MB)
- **Extraction**: Always from full quality with `-c copy` (lossless)
- **Aspect ratio**: Maintain 9:16 throughout

### Gemini Integration
- Models: `gemini-2.5-pro` (main pipeline), `gemini-2.5-flash` (GIF analysis)
- Max output tokens: 65,536 (64K supported)
- Upload strategy: Direct if <100MB, else Digital Ocean Spaces
- Response validation: Strict JSON schema with timestamps
- Structured output with response_mime_type: "application/json"

### Voiceover Mode
- Uses OpenAI Whisper for transcription
- Provides exact segment timing from audio
- Overrides Gemini's auto-segmentation
- Ensures perfect audio-visual sync

### Error Handling
- Keeps `merged_full.mp4` on errors for manual recovery
- Validates all timestamps before extraction
- Falls back to standard mode if voiceover fails
- Implements retry with extreme compression for large files

## Common Tasks

### Adding a New Video Service
1. Create service in `backend/services/` extending `BaseService`
2. Add to `VideoProcessingWorkflow` or `GeminiAnalysisWorkflow`
3. Update `PipelineOrchestrator` if needed

### Modifying Gemini Prompts
Edit `backend/core/gemini_client.py`:
- `create_prompt_for_json()` - Main analysis prompt
- `create_voiceover_prompt()` - Voiceover mode prompt

### Adding Frontend Components
```bash
# Add new shadcn component
npx shadcn@latest add [component-name]

# Components go in:
# - app/components/ (main app)
# - frontend/components/ (toolkit)
```

### Debugging Pipeline Issues
1. Enable debug mode: `DEBUG_MODE=true` in backend/.env
2. Check logs in `backend/logs/`
3. Review debug data in `output/debug_*.json`
4. Keep `backend/temp/merged_full_*.mp4` for manual inspection

## Performance Targets
- Total pipeline: <5 minutes
- Compressed file: <100MB
- Gemini processing: <2 minutes
- Output accuracy: ±3 seconds of target
- Frontend load: <3s initial, <100ms interactions