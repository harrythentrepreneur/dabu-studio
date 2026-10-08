# Dabu Backend - RunPod Video Processing Service

Backend service for Dabu TikTok video ad automation, designed to run on RunPod serverless infrastructure.

## Overview

This backend handles:
- **Express Builder**: AI-powered video compilation with script matching
- **Quick Create**: Express Builder + automated caption generation via CapCut
- **Video Processing**: FFmpeg-based video merging and extraction
- **AI Analysis**: Google Gemini integration for intelligent script-to-video matching
- **Voiceover Support**: OpenAI Whisper API for audio synchronization

## Architecture

```
backend/
├── runpod/
│   └── worker/
│       └── main_handler.py      # RunPod entry point
├── main.py                       # Express Builder pipeline
├── core/                         # Core processing logic
├── services/                     # Modular services
├── business/                     # Business logic orchestration
└── utils/                        # Utilities and helpers
```

## Deployment

### RunPod Setup

1. Create a RunPod serverless endpoint
2. Deploy this code as a Docker container or zip file
3. Set environment variables in RunPod dashboard
4. Update frontend with RunPod endpoint ID

### Environment Variables

Copy `.env.example` to `.env` and configure your values.

## API Interface

The backend receives jobs from the frontend via RunPod API.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Test pipeline locally
python main.py --script input_videos/script.txt --duration 35
```

## Support

For issues or questions, please open an issue on GitHub.
