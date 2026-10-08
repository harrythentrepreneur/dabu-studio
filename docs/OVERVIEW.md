# TikTok Video Ad Automation

AI-powered video automation tool that transforms scripts into compiled TikTok-ready videos using Google Gemini API for intelligent scene matching and RunPod for scalable GPU-accelerated video processing.

## 🎯 What It Does

Transform your script and raw video footage into a polished TikTok ad:
- **Input**: Your ad script + multiple video files
- **AI Analysis**: Gemini finds the perfect moments for each script line
- **Output**: Professional video with hard cuts, ready for TikTok

## ✨ Key Features

- 🤖 **AI-Powered Matching** - Gemini 2.0 analyzes videos and matches script emotions
- 🎬 **Smart Segmentation** - Automatic 5-8 second segments with optimal cut points
- 🎙️ **Voiceover Mode** - Perfect sync with pre-recorded audio using Whisper API
- ⚡ **Serverless GPU Processing** - RunPod workers scale from 0 to handle any load
- 📊 **Real-Time Progress** - Live updates via Server-Sent Events
- 🎨 **Dual Frontend Apps** - Main automation UI + Extended creative toolkit
- 💰 **Cost-Effective** - Pay only for GPU seconds used (as low as $0.00011/sec)
- 🚀 **Fast Processing** - Under 5 minutes for most projects

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Frontend Apps  │────▶│  Flask API       │────▶│  RunPod Workers │
│  (Next.js)      │     │  (Lightweight)   │     │  (GPU-Powered)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐         ┌──────────────┐
                        │    Redis     │         │  Gemini API  │
                        │  (SSE/Cache) │         │   (AI Brain) │
                        └──────────────┘         └──────────────┘
```

### Deployment Options

- **Local Development**: Docker Compose for all services
- **Production**: 
  - Flask API on Railway/Render ($5/month)
  - RunPod serverless workers (pay-per-use)
  - Frontend on Vercel (free tier)

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- Node.js 18+ and npm
- Python 3.9+
- Google Gemini API key
- RunPod account (for production)

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/harrythentrepreneur/dabu-studio.git
cd tiktok-video-ad-automation

# Set up environment
cd backend
cp .env.example .env
# Edit .env with your API keys
cd ..

# Start everything
docker-compose up
```

Access:
- Main App: http://localhost:3000
- Toolkit: http://localhost:3002  
- API: http://localhost:5000

### Option 2: Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend - Main App (new terminal)
cd app
npm install
npm run dev

# Frontend - Toolkit (new terminal)
cd frontend
npm install  
npm run dev -- --port 3002
```

## 📁 Project Structure

```
tiktok-video-ad-automation/
│
├── app/                  # Main Next.js app - Video automation UI
│   ├── page.tsx         # Main interface
│   └── components/      # React components with shadcn/ui
│
├── frontend/            # Extended toolkit app (separate Next.js)
│   ├── app/            # Advanced features
│   │   ├── express-builder/  # Quick video creation
│   │   ├── clip-studio/     # Video editing tools
│   │   └── gif-studio/      # GIF extraction
│   └── components/     # Toolkit components
│
├── backend/            # Python API & processing
│   ├── api/           # Flask REST endpoints
│   ├── core/          # Video processing & Gemini
│   ├── services/      # Business logic
│   ├── runpod_worker/ # RunPod serverless worker
│   ├── runpod_client/ # RunPod API client
│   ├── config/        # Settings & constants
│   └── app.py         # API entry point
│
├── input_videos/       # Your source videos go here
├── output/            # Generated videos appear here
│
├── docker-compose.yml # Local development setup
├── CLAUDE.md          # AI assistant instructions
├── start.sh           # Quick start script
└── README.md          # This file
```

## 🎬 How It Works

### Standard Workflow

1. **Upload** your script and videos through the web UI
2. **AI analyzes** your content:
   - Merges videos into a single timeline
   - Creates compressed version for Gemini
   - AI matches script lines to video moments
3. **Processing** extracts perfect segments
4. **Export** final video with your script timing

### Voiceover Workflow

1. **Upload** script, videos, and voiceover audio
2. **Whisper API** extracts exact timing from audio
3. **AI matches** visuals to audio segments
4. **Export** video perfectly synced to voiceover

## 🛠️ API Documentation

### Main Processing Endpoint

`POST http://localhost:5000/api/process`

```json
{
  "script": "Your TikTok ad script...",
  "videos": ["video1.mp4", "video2.mp4"],
  "target_duration": 30,
  "voiceover_path": "optional_audio.mp3"
}
```

### Real-Time Updates

`GET http://localhost:5000/api/status-stream/{request_id}`

Provides Server-Sent Events with processing progress:
```
data: {"step": 2, "total": 10, "message": "Analyzing with AI", "progress": 20}
```

### Download Results

`GET http://localhost:5000/api/download/{request_id}/video`

File types: `video`, `script`, `timestamps`, `voiceover`, `debug`

## 🎨 Frontend Applications

### Main App (Root)
The primary interface for video automation:
- Script input with character counter
- Drag-and-drop video upload
- Real-time processing status
- Download generated videos

**Tech**: Next.js 15, shadcn/ui, Tailwind CSS

### Extended Toolkit (`/frontend`)
Advanced creative tools:
- **Express Builder** - Quick video creation from templates
- **Clip Studio** - Advanced editing capabilities  
- **GIF Studio** - Extract perfect GIF moments
- **Analytics** - Performance tracking

**Access**: http://localhost:3002 (when running)

## ⚙️ Configuration

### Video Processing Settings

Edit `backend/config/constants.py`:

```python
VIDEO_CONSTANTS = {
    'MAX_FILE_SIZE': 2GB,
    'TARGET_RESOLUTION': (1080, 1920),  # 9:16
    'COMPRESSION_CRF': 28,
    'OUTPUT_DURATION_TOLERANCE': 3.0    # ±3 seconds
}
```

### Gemini AI Settings

Model: `gemini-2.0-flash-exp`
- Temperature: 0.2 (deterministic)
- Max tokens: 65,536
- Structured JSON output

## 📊 Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Total processing | <5 min | 2-3 min |
| Video compression | 30:1 ratio | 25-35:1 |
| AI analysis | <2 min | 45-90s |
| Output accuracy | ±3 seconds | ±1.5s |

## 🔍 Debugging

### Enable Debug Mode

```bash
# In backend/.env
DEBUG_MODE=true
```

This creates detailed debug files in `output/debug_*.json`

### View Logs

```bash
# Backend logs
tail -f backend/logs/main.log

# Error logs
tail -f backend/logs/main_errors.log

# All logs
./logs.sh
```

### Common Issues

**"Gemini upload failed"**
- Ensure video is <100MB after compression
- Check API key is valid

**"Duration mismatch"**
- Adjust tolerance in `backend/config/constants.py`
- Ensure enough source video footage

**"FFmpeg error"**
- Verify FFmpeg installation: `ffmpeg -version`
- Check file formats are supported

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
pytest --cov=backend  # With coverage
```

### Mock Mode (No API calls)
```bash
python backend/main.py --mock
```

### Frontend Tests
```bash
npm test
npm run test:e2e  # End-to-end tests
```

## 📝 Development

### Code Style

**Backend (Python)**:
```bash
black backend/       # Format code
flake8 backend/     # Lint
mypy backend/       # Type checking
```

**Frontend (TypeScript)**:
```bash
npm run lint        # ESLint
npm run format      # Prettier
```

### Adding Features

1. **New API Endpoint**: Add to `backend/api/request_handlers.py`
2. **New Service**: Create in `backend/services/` extending `BaseService`
3. **Frontend Component**: Use `npx shadcn@latest add [component]`
4. **New Workflow**: Extend `backend/business/base_workflow.py`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Follow existing patterns and style
4. Add tests for new features
5. Update documentation
6. Submit pull request

### Guidelines

- Use type hints in Python
- Add JSDoc comments in TypeScript
- Follow REST conventions for APIs
- Maintain 9:16 aspect ratio
- Test with multiple video formats

## 📚 Tech Stack Details

### Backend
- **Flask** - REST API framework
- **Google Gemini** - AI video analysis
- **FFmpeg** - Video processing
- **Pydantic** - Data validation
- **OpenAI Whisper** - Audio transcription
- **Boto3** - Cloud storage

### Frontend
- **Next.js 15** - React framework
- **shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety
- **React Hook Form** - Form handling
- **Zod** - Schema validation

### Infrastructure
- **Digital Ocean Spaces** - Large file storage
- **Server-Sent Events** - Real-time updates
- **Docker** - Containerization (optional)

## 🔒 Security

- API keys stored in environment variables
- Input validation on all endpoints
- File type/size restrictions
- Sanitized FFmpeg commands
- No direct file system access from API

## 📈 Roadmap

- [ ] Batch processing for multiple ads
- [ ] Custom style templates
- [ ] Music library integration
- [ ] Advanced transitions
- [ ] Cloud deployment
- [ ] Mobile app
- [ ] Team collaboration features

## 📞 Support

- Check `./logs.sh` for debugging
- Review `backend/docs/` for detailed guides
- See `CLAUDE.md` for AI assistant help

## 📄 License

Copyright 2025 - TikTok Video Ad Automation

---

Built with ❤️ for content creators who value their time.