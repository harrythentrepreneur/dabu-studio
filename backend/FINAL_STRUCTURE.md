# Final Backend Structure for RunPod

## What This Backend Does

1. **Receives requests from frontend** via RunPod API
2. **Processes Express Builder** - Script + Videos → Compiled Video
3. **Processes Quick Create** - Same as Express Builder + CapCut captions

## Core Files Structure

```
backend/
├── runpod/
│   └── worker/
│       └── main_handler.py      # ← MAIN ENTRY POINT (listens to frontend)
├── main.py                       # Express Builder pipeline
├── core/
│   ├── video_processor.py       # FFmpeg video processing
│   ├── gemini_client.py         # AI script analysis
│   └── pipeline.py              # Pipeline orchestration
├── services/
│   ├── video_merger_service.py  # Merge multiple videos
│   ├── video_extractor_service.py # Extract segments
│   ├── voiceover_analyzer.py    # Whisper API
│   ├── intelligent_capcut_service.py # CapCut automation for Quick Create
│   ├── browser_orchestrator.py  # Browser automation
│   ├── virtual_display_manager.py # Headless display
│   └── cloud_storage_service.py # DO Spaces upload/download
├── business/
│   └── pipeline_orchestrator.py # Business logic
├── config/
│   └── settings.py              # Configuration
└── utils/
    └── logger.py                # Logging
```

## How It Works

### Frontend Request Flow:
```
1. Frontend uploads files to DO Spaces
2. Frontend sends request to RunPod:
   POST https://api.runpod.ai/v2/{endpoint}/runsync
   {
     "input": {
       "request_id": "xxx",
       "task_type": "express_builder" or "quick_create",
       "script": "text",
       "videos": ["DO_Spaces_URLs"],
       "duration": 30
     }
   }

3. RunPod worker (main_handler.py) receives request
4. Downloads videos from DO Spaces
5. Processes based on task_type:
   - express_builder: Compile video
   - quick_create: Compile + Add captions via CapCut
6. Uploads results to DO Spaces
7. Returns URLs to frontend
```

### Response:
```json
{
  "success": true,
  "videoUrl": "https://spaces.../output.mp4",
  "scriptUrl": "https://spaces.../script.txt",
  "timestampsUrl": "https://spaces.../timestamps.json",
  "captionedVideoUrl": "https://spaces.../captioned.mp4" // if quick_create
}
```

## Essential Services Only

- **Video Processing**: FFmpeg operations
- **AI Analysis**: Gemini for script-to-video matching
- **CapCut Automation**: For Quick Create captions
- **Storage**: DO Spaces integration
- **Voiceover**: Whisper API (if voiceover provided)

## No Flask, No APIs

- RunPod handles all HTTP communication
- Backend is purely processing logic
- Frontend talks directly to RunPod API
- RunPod invokes our handler function