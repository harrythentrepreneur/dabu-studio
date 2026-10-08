# API Documentation

Complete API reference for TikTok Video Ad Automation backend services.

## Base URL

- **Local Development**: `http://localhost:5000`
- **Production**: `https://your-api-domain.com`

## Authentication

Currently, the API does not require authentication for local development. In production, implement API key authentication:

```http
Authorization: Bearer YOUR_API_KEY
```

## Content Types

- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

## API Endpoints

### Core Processing

#### Process Video (Local)

Process video using local FFmpeg and Gemini API.

```http
POST /api/process
```

**Request Body:**
```json
{
  "script": "Line 1 of your script.\nLine 2 of your script.",
  "videos": ["path/to/video1.mp4", "path/to/video2.mp4"],
  "target_duration": 30,
  "voiceover_path": "path/to/voiceover.mp3"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "request_id": "uuid-v4-string",
  "message": "Processing started"
}
```

#### Process Video (RunPod)

Process video using RunPod serverless workers.

```http
POST /api/process/runpod
```

**Request Body:**
```json
{
  "script": "Your script text",
  "videos": ["https://url-to-video1.mp4", "https://url-to-video2.mp4"],
  "duration": 30,
  "voiceover": "https://url-to-voiceover.mp3",  // Optional
  "request_id": "custom-request-id"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "request_id": "uuid-v4-string",
  "output": {
    "video_url": "https://storage.url/final.mp4",
    "segments": [...],
    "metadata": {...}
  }
}
```

### Status & Monitoring

#### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "gemini": "connected",
    "runpod": "connected",
    "redis": "connected"
  }
}
```

#### Status Stream (SSE)

Real-time processing updates via Server-Sent Events.

```http
GET /api/status-stream/<request_id>
```

**Response (SSE Stream):**
```
event: status
data: {"step": "initialization", "message": "Starting processing", "progress": 0}

event: status
data: {"step": "merging", "message": "Merging videos", "progress": 20}

event: status
data: {"step": "completed", "message": "Processing complete", "progress": 100}
```

#### Get Request Status

```http
GET /api/status/<request_id>
```

**Response:**
```json
{
  "request_id": "uuid-v4-string",
  "status": "processing",
  "progress": 45,
  "current_step": "ai_analysis",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:30Z"
}
```

### Results & Downloads

#### Get Result

```http
GET /api/result/<request_id>
```

**Response:**
```json
{
  "request_id": "uuid-v4-string",
  "status": "completed",
  "outputs": {
    "video": "path/to/final.mp4",
    "script": "path/to/script.txt",
    "timestamps": "path/to/timestamps.json",
    "voiceover": "path/to/voiceover.mp3"
  },
  "metadata": {
    "duration": 30.5,
    "segments_count": 6,
    "processing_time": 145.3
  }
}
```

#### Download File

```http
GET /api/download/<request_id>/<file_type>
```

**File Types:**
- `video` - Final processed video
- `script` - Script text file
- `timestamps` - JSON with segment timestamps
- `voiceover` - Audio file (if provided)
- `debug` - Debug information (if debug mode enabled)

**Response:**
- Content-Type: `video/mp4`, `text/plain`, `application/json`, or `audio/mpeg`
- Content-Disposition: `attachment; filename="output.mp4"`

### RunPod Specific Endpoints

#### RunPod Configuration

```http
GET /api/runpod/config
```

**Response:**
```json
{
  "configured": true,
  "endpoint_id": "your-endpoint-id",
  "base_url": "https://api.runpod.ai/v2",
  "timeout": 600,
  "mode": "serverless"
}
```

#### RunPod Health

```http
GET /api/runpod/health
```

**Response:**
```json
{
  "status": "healthy",
  "workers": {
    "available": 3,
    "busy": 1,
    "total": 4
  },
  "queue": {
    "pending": 2,
    "processing": 1
  }
}
```

#### RunPod Job Status

```http
GET /api/runpod/status/<job_id>
```

**Response:**
```json
{
  "job_id": "job-uuid",
  "status": "IN_PROGRESS",
  "progress": 60,
  "created_at": "2024-01-15T10:30:00Z",
  "execution_time": 45.2
}
```

#### Cancel RunPod Job

```http
POST /api/runpod/cancel/<job_id>
```

**Response:**
```json
{
  "status": "success",
  "message": "Job cancelled"
}
```

### Task-Specific Endpoints

#### Merge Videos

```http
POST /api/runpod/merge
```

**Request Body:**
```json
{
  "videos": ["url1.mp4", "url2.mp4", "url3.mp4"],
  "request_id": "custom-id"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "output_url": "https://storage.url/merged.mp4",
  "file_size": 104857600
}
```

#### Compress Video

```http
POST /api/runpod/compress
```

**Request Body:**
```json
{
  "video": "https://url-to-video.mp4",
  "target_size_mb": 100,  // Optional, default 100
  "request_id": "custom-id"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "output_url": "https://storage.url/compressed.mp4",
  "file_size": 95000000,
  "compression_ratio": 3.2
}
```

#### Extract Segments

```http
POST /api/runpod/extract
```

**Request Body:**
```json
{
  "video": "https://url-to-video.mp4",
  "segments": [
    {
      "start": 0.0,
      "end": 5.5,
      "text": "First segment text"
    },
    {
      "start": 10.2,
      "end": 15.8,
      "text": "Second segment text"
    }
  ],
  "request_id": "custom-id"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "segments": [
    {
      "index": 0,
      "url": "https://storage.url/segment_0.mp4",
      "start": 0.0,
      "end": 5.5,
      "text": "First segment text"
    }
  ],
  "final_video_url": "https://storage.url/final.mp4"
}
```

#### Add Voiceover

```http
POST /api/runpod/voiceover
```

**Request Body:**
```json
{
  "video": "https://url-to-video.mp4",
  "audio": "https://url-to-audio.mp3",
  "request_id": "custom-id"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "output_url": "https://storage.url/with_voiceover.mp4"
}
```

### Validation

#### Validate Input

```http
POST /api/validate
```

**Request Body:**
```json
{
  "script": "Your script text",
  "videos": ["video1.mp4", "video2.mp4"],
  "target_duration": 30
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Target duration is close to maximum allowed"
  ],
  "metadata": {
    "script_length": 150,
    "video_count": 2,
    "estimated_processing_time": 120
  }
}
```

### Creative Tools

#### GIF Studio Analysis

```http
POST /api/gif-studio/analyze
```

**Request Body:**
```json
{
  "script": "Your script text for GIF analysis"
}
```

**Response:**
```json
{
  "gif_moments": [
    {
      "text": "This would make a great GIF",
      "reason": "High energy, repeatable action",
      "duration": 3,
      "style": "energetic",
      "loop_type": "bounce"
    }
  ]
}
```

#### Clip Studio Analysis

```http
POST /api/clip-studio/analyze
```

**Request Body:**
```json
{
  "script": "Your script for clip extraction"
}
```

**Response:**
```json
{
  "clips": [
    {
      "title": "Opening Hook",
      "description": "Attention-grabbing opener",
      "duration": 5,
      "importance": "high"
    }
  ]
}
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error context"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `MISSING_FIELD` | 400 | Required field missing |
| `FILE_TOO_LARGE` | 413 | File exceeds size limit |
| `PROCESSING_FAILED` | 500 | Video processing error |
| `GEMINI_ERROR` | 503 | Gemini API error |
| `RUNPOD_ERROR` | 503 | RunPod service error |
| `NOT_FOUND` | 404 | Resource not found |
| `TIMEOUT` | 504 | Processing timeout |

## Rate Limiting

Production deployments should implement rate limiting:

- **Standard**: 100 requests per minute
- **Processing**: 10 concurrent processing jobs
- **Downloads**: 1000 requests per hour

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Webhooks

Configure webhooks for async processing notifications:

```json
{
  "webhook_url": "https://your-server.com/webhook",
  "events": ["processing.started", "processing.completed", "processing.failed"],
  "secret": "your-webhook-secret"
}
```

Webhook payload:
```json
{
  "event": "processing.completed",
  "request_id": "uuid-v4-string",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "status": "success",
    "output_url": "https://storage.url/final.mp4"
  }
}
```

## SDK Examples

### Python

```python
import requests

class TikTokVideoAPI:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def process_video(self, script, videos, duration=30):
        response = requests.post(
            f"{self.base_url}/api/process/runpod",
            json={
                "script": script,
                "videos": videos,
                "duration": duration
            }
        )
        return response.json()
    
    def get_status(self, request_id):
        response = requests.get(
            f"{self.base_url}/api/status/{request_id}"
        )
        return response.json()

# Usage
api = TikTokVideoAPI()
result = api.process_video(
    script="Your amazing script",
    videos=["video1.mp4", "video2.mp4"],
    duration=30
)
```

### JavaScript/TypeScript

```typescript
class TikTokVideoAPI {
  constructor(private baseUrl = 'http://localhost:5000') {}
  
  async processVideo(script: string, videos: string[], duration = 30) {
    const response = await fetch(`${this.baseUrl}/api/process/runpod`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script, videos, duration })
    });
    return response.json();
  }
  
  async streamStatus(requestId: string, onUpdate: (data: any) => void) {
    const eventSource = new EventSource(
      `${this.baseUrl}/api/status-stream/${requestId}`
    );
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onUpdate(data);
    };
    
    return eventSource;
  }
}

// Usage
const api = new TikTokVideoAPI();
const result = await api.processVideo(
  'Your script',
  ['video1.mp4', 'video2.mp4'],
  30
);
```

### cURL

```bash
# Process video
curl -X POST http://localhost:5000/api/process/runpod \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Your script text",
    "videos": ["video1.mp4", "video2.mp4"],
    "duration": 30
  }'

# Get status
curl http://localhost:5000/api/status/REQUEST_ID

# Stream updates
curl -N http://localhost:5000/api/status-stream/REQUEST_ID
```

## Testing

### Postman Collection

Import the [Postman collection](../postman/tiktok-video-api.json) for easy testing.

### Test Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Validate input
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"script": "Test", "videos": ["test.mp4"], "target_duration": 30}'
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- RunPod integration
- SSE streaming support
- GIF/Clip studio endpoints