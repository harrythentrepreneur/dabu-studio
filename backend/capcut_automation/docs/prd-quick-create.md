# CapCut Auto-Captions Integration PRD
## TikTok Video Ad Automation with Professional Captions

### Executive Summary
Two separate but integrated frontend experiences:
1. **Express Builder**: Current video generation pipeline (Script → Gemini → Compiled Video with Voiceover)
2. **Quick Create**: Extended pipeline with CapCut auto-captions (Takes Express Builder output → CapCut Auto-Transcribe → Captioned Video + Project Files)

Both share the same backend processing pipeline, with Quick Create continuing where Express Builder completes.

---

## Architecture Overview

### Frontend Structure
```
frontend/app/(toolkit)/
├── express-builder/        # EXISTING - Current video generation
│   └── page.tsx           # Script + Videos → Compiled video with voiceover
├── quick-create/          # TO BE CREATED - CapCut integration
│   ├── page.tsx          # TO BE CREATED - Same inputs, extended processing
│   └── components/       # TO BE CREATED - All components below
│       ├── caption-style-selector.tsx
│       ├── capcut-status.tsx
│       ├── project-download.tsx
│       └── caption-preview.tsx
```

### Processing Flow

#### Tab 1: Express Builder (Current)
- **Input**: Script + Videos + Optional Voiceover
- **Process**: Gemini API matching + voiceover sync
- **Output**: Compiled video with perfect voiceover sync, timestamps, script
- **Use Case**: Quick video generation without captions

#### Tab 2: Quick Create (New)
- **Input**: Script + Videos + Optional Voiceover + **Caption Style Selection (TikTok styles)**
- **Backend Process**: 
  1. Runs complete Express Builder pipeline (steps 1-10)
  2. Takes the output video (with voiceover already synced)
  3. Applies CapCut auto-transcribe for captions (steps 11-14)
- **Output**: Everything from Express + Captioned video + CapCut project files (ZIP)
- **Use Case**: Complete TikTok-ready videos with professional captions

---

## Quick Create Implementation

### Implementation Status
**⚠️ NOTE: All components below need to be created. They do not currently exist in the codebase.**

### Phase 1: Backend Extension - Continuation Architecture

#### NEW FILE: Processing Pipeline - Continuation Model
```python
# backend/capcut_processor.py (TO BE CREATED)
class CapCutProcessor:
    def __init__(self, compiled_video_path, caption_style='TikTok Bold'):
        """
        Initialize with the OUTPUT from Express Builder pipeline.
        The video already has voiceover perfectly synced.
        """
        self.input_video = compiled_video_path  # Already has voiceover
        self.caption_style = caption_style
        self.docker_enabled = os.getenv('CAPCUT_DOCKER', 'false') == 'true'
    
    def apply_auto_transcribe(self):
        """
        Apply CapCut auto-transcribe to the finished video.
        This analyzes the audio track and generates captions.
        """
        if self.docker_enabled:
            return self.run_in_docker()
        else:
            return self.run_local()
    
    def run_in_docker(self):
        """Execute CapCut in Docker container for server deployment."""
        # Docker implementation for server-side execution
        pass
```

#### MODIFY EXISTING: Backend Flow - Shared Pipeline
```python
# Modify existing backend/app.py endpoint
# Quick Create uses the SAME backend endpoint
# but with additional processing flag

@app.route('/api/process', methods=['POST'])  # EXISTING ENDPOINT - NEEDS MODIFICATION
def process_video():
    # Check if this is for Quick Create
    apply_captions = request.form.get('apply_captions', 'false') == 'true'
    caption_style = request.form.get('caption_style', 'TikTok Bold')
    
    # Run standard Express Builder pipeline (steps 1-10)
    result = run_standard_pipeline(request)
    
    if apply_captions and result.success:
        # Continue with CapCut processing (steps 11-14)
        capcut_processor = CapCutProcessor(
            compiled_video_path=result.video_path,
            caption_style=caption_style
        )
        capcut_result = capcut_processor.apply_auto_transcribe()
        result.update(capcut_result)
    
    return result
```

### Phase 2: Frontend Quick Create Page

#### NEW FILES: Component Structure
```typescript
// frontend/app/(toolkit)/quick-create/page.tsx (TO BE CREATED)
export default function QuickCreatePage() {
  // Same base functionality as Express Builder
  const [script, setScript] = useState("");
  const [videos, setVideos] = useState<File[]>([]);
  const [voiceover, setVoiceover] = useState<File | null>(null);
  
  // Additional CapCut specific state
  const [captionStyle, setCaptionStyle] = useState("TikTok Bold");
  const [captionStyles] = useState([
    'TikTok Bold',
    'TikTok Pop', 
    'TikTok Glow',
    'TikTok Classic',
    'TikTok Neon'
  ]);
  
  const handleProcess = async () => {
    const formData = new FormData();
    formData.append('script', script);
    formData.append('apply_captions', 'true'); // Flag for Quick Create
    formData.append('caption_style', captionStyle);
    videos.forEach(v => formData.append('videos', v));
    if (voiceover) formData.append('voiceover', voiceover);
    
    // Uses SAME endpoint as Express Builder
    const response = await fetch('/api/process', {
      method: 'POST',
      body: formData
    });
  };
  
  return (
    <>
      {/* Caption Style Selector - NEW */}
      <CaptionStyleSelector 
        styles={captionStyles}
        selected={captionStyle}
        onChange={setCaptionStyle}
      />
      {/* Rest same as Express Builder */}
    </>
  );
}
```

### Phase 3: Processing Steps Display

#### Express Builder (10 steps)
1. Loading inputs
2. Merging videos (full quality)
3. Compressing for AI
4. Uploading to Gemini
5. AI Analysis
6. Validating timestamps
7. Extracting segments
8. Compiling final video
9. Adding voiceover (if provided)
10. Cleanup

#### Quick Create (14 steps)
Steps 1-10: Complete Express Builder pipeline
11. **Initializing CapCut** (NEW)
12. **Auto-Transcribing Audio** (NEW) - Analyzes the voiceover/audio track
13. **Applying Caption Style** (NEW) - User-selected TikTok style
14. **Exporting & Packaging** (NEW) - Video + Project files in ZIP

### Phase 4: Server Deployment - Hetzner Cloud (Option 1)

#### Production Architecture
```yaml
# We're using Hetzner Cloud for cost-effective deployment
Backend Server (Linux):
  - Provider: Hetzner Cloud
  - Type: CX21
  - OS: Ubuntu 22.04
  - Cost: €5.83/month
  - Runs: Python Flask, Gemini API, FFmpeg (Steps 1-10)

CapCut Server (Windows):
  - Provider: Hetzner Cloud  
  - Type: CPX31
  - OS: Windows Server 2022
  - Cost: €45.73/month
  - Runs: CapCut + PyAutoGUI (Steps 11-14)

Total: €51.56/month (~$56)
```

#### NEW FILE: Windows Server Integration
```python
# backend/services/hetzner_capcut_service.py (TO BE CREATED)
class HetznerCapCutService:
    """
    Service that connects Linux backend to Windows CapCut server.
    No Docker needed - direct Windows Server with PyAutoGUI.
    """
    def __init__(self):
        # Windows server configuration from environment
        self.windows_server = {
            'host': os.environ.get('CAPCUT_WINDOWS_IP'),
            'port': 8080,
            'api_key': os.environ.get('CAPCUT_API_KEY')
        }
    
    def process_video_with_captions(self, video_path, caption_style):
        """Send video to Windows server for CapCut processing."""
        # Upload video to Windows server
        with open(video_path, 'rb') as f:
            response = requests.post(
                f"http://{self.windows_server['host']}:{self.windows_server['port']}/upload",
                files={'video': f}
            )
        
        # Trigger CapCut automation
        job_response = requests.post(
            f"http://{self.windows_server['host']}:{self.windows_server['port']}/process",
            json={
                'video_path': response.json()['path'],
                'caption_style': caption_style
            }
        )
        
        # Poll for completion and download results
        return self.wait_and_download(job_response.json()['job_id'])
```

### Phase 5: CapCut Automation Details

#### Configuration Structure
```json
{
  "source": "quick_create",
  "video": "/output/compiled_video_with_voiceover.mp4",
  "caption_style": "TikTok Bold",
  "auto_captions": {
    "enabled": true,
    "language": "auto",
    "mode": "transcribe"  // Not translate, just transcribe
  },
  "export_settings": {
    "preset": "TikTok-1080x1920",
    "quality": "high",
    "fps": 30,
    "bitrate": "10M"
  },
  "outputs": {
    "video_path": "/output/final_captioned.mp4",
    "project_path": "/output/project.capcut",
    "save_assets": true
  }
}
```

#### NEW FILE: Local Automation Script (Mac)
```python
# backend/capcut_automation/mac_automation.py (TO BE CREATED)
import subprocess
import time
from pathlib import Path

class MacCapCutAutomation:
    def __init__(self, video_path, caption_style):
        self.video_path = video_path
        self.caption_style = caption_style
        
    def run_automation(self):
        """Run CapCut automation using AppleScript."""
        script = f'''
        tell application "CapCut"
            activate
            
            -- Create new project
            tell application "System Events"
                keystroke "n" using command down
                delay 2
                
                -- Import video
                keystroke "i" using command down
                delay 1
                keystroke "{self.video_path}"
                keystroke return
                delay 3
                
                -- Add to timeline
                key code 36 -- Enter
                delay 2
                
                -- Trigger Auto Transcribe
                click menu item "Auto Captions" of menu "Text"
                delay 1
                click button "Generate"
                
                -- Wait for transcription
                delay 15
                
                -- Apply style
                click button "Style"
                keystroke "{self.caption_style}"
                key code 36 -- Select
                
                -- Export
                keystroke "e" using command down
            end tell
        end tell
        '''
        
        subprocess.run(['osascript', '-e', script])
```

### Phase 6: Error Handling & Developer-Focused Debug Logging

#### NEW FILE: Detailed Error Logging for Debugging
```python
# backend/capcut_error_handler.py (TO BE CREATED)
class CapCutErrorHandler:
    def __init__(self, request_id):
        self.request_id = request_id
        self.log_file = f'/logs/capcut_{request_id}.log'
        self.errors = []
        self.debug_mode = True  # Always verbose for development
    
    def log_error(self, step, error, context=None):
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'step_name': self.get_step_name(step),
            'error': str(error),
            'error_type': type(error).__name__,
            'context': context,
            'traceback': traceback.format_exc(),
            # Developer-focused details
            'system_info': {
                'platform': platform.system(),
                'capcut_version': os.getenv('CAPCUT_VERSION'),
                'docker': os.path.exists('/.dockerenv'),
                'display': os.getenv('DISPLAY'),
            },
            'automation_state': {
                'last_successful_action': self.last_success,
                'screenshot_path': self.capture_screenshot(),
                'window_hierarchy': self.get_window_tree(),
            }
        }
        self.errors.append(error_entry)
        
        # Console output for terminal debugging
        print(f"\n{'='*60}")
        print(f"ERROR at Step {step} ({self.get_step_name(step)})")
        print(f"{'='*60}")
        print(f"Type: {error_entry['error_type']}")
        print(f"Message: {error}")
        print(f"Context: {json.dumps(context, indent=2)}")
        print(f"Screenshot: {error_entry['automation_state']['screenshot_path']}")
        print(f"Full log: {self.log_file}")
        print(f"{'='*60}\n")
        
        # Write detailed log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(error_entry, indent=2))
            f.write('\n---\n')
    
    def capture_screenshot(self):
        """Capture current screen state for debugging."""
        screenshot_path = f'/logs/screenshots/{self.request_id}_{datetime.now().timestamp()}.png'
        # Implementation depends on platform
        return screenshot_path
```

### Phase 7: Results Display Enhancement

#### Quick Create Results Page
```typescript
interface QuickCreateResult {
  // Standard results (shared with Express)
  videoUrl: string;
  scriptUrl: string;
  timestampsUrl: string;
  
  // CapCut specific
  captionedVideoUrl: string;
  projectBundleUrl: string;  // ZIP file
  captionMetadata: {
    style: string;
    language: string;
    wordCount: number;
    duration: number;
  };
}
```

#### Download Options - ZIP Bundle
```typescript
// All files packaged in single ZIP download
interface ProjectBundle {
  'captioned_video.mp4': File;        // Final video with captions
  'project.capcut': File;              // CapCut project file
  'assets/': {                         // Source materials
    'original_video.mp4': File;        // Video with voiceover (no captions)
    'script.txt': File;                // Original script
    'timestamps.json': File;           // Segment timestamps
    'caption_style.json': File;        // Style configuration
  };
  'logs/': {                           // For debugging
    'processing.log': File;            // Full processing log
    'capcut_automation.log': File;     // CapCut specific log
  };
}

// Frontend download handler
const downloadProjectBundle = async () => {
  const response = await fetch(`/api/download/${requestId}/bundle`);
  const blob = await response.blob();
  
  // Create download link
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `quick_create_${requestId}.zip`;
  a.click();
};
```

### Phase 8: Caption Style Selection UI

#### NEW FILE: Caption Style Component
```typescript
// frontend/app/(toolkit)/quick-create/components/caption-style-selector.tsx (TO BE CREATED)
export function CaptionStyleSelector({ 
  selected, 
  onChange, 
  styles 
}: CaptionStyleProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Caption Style</CardTitle>
        <CardDescription>
          Choose your TikTok caption style
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={selected} onValueChange={onChange}>
          {styles.map(style => (
            <div key={style} className="flex items-center space-x-2">
              <RadioGroupItem value={style} id={style} />
              <Label htmlFor={style}>
                {style}
                <span className="text-xs text-muted-foreground ml-2">
                  {getStyleDescription(style)}
                </span>
              </Label>
            </div>
          ))}
        </RadioGroup>
      </CardContent>
    </Card>
  );
}
```

### Phase 9: SSE Status Updates

#### Additional Status Events for CapCut
```typescript
// Status updates for steps 11-14
const capcutStatusEvents = [
  { step: 11, message: "Initializing CapCut...", progress: 72 },
  { step: 12, message: "Auto-transcribing audio track...", progress: 80 },
  { step: 13, message: "Applying ${captionStyle} style...", progress: 88 },
  { step: 14, message: "Packaging project files...", progress: 95 }
];

// Backend emitter
class StatusEmitter:
    def emit_capcut_status(self, step, message, progress):
        self.emit({
            'step': step,
            'step_name': f'capcut_step_{step-10}',
            'message': message,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        })
```

### Phase 10: User Experience Differences

#### Express Builder
- **Speed**: 3-5 minutes
- **Output**: Professional compiled video with synced voiceover
- **Best for**: Quick iterations, testing scripts
- **Post-process**: Manual caption addition if needed

#### Quick Create
- **Speed**: 5-7 minutes (additional 2-3 min for auto-transcribe)
- **Output**: TikTok-ready video with native captions + project files
- **Best for**: Final production, direct upload to TikTok
- **Post-process**: Open project file in CapCut for fine-tuning

### Phase 11: Data Persistence & Storage Management

#### Video Cache Extension
```typescript
interface VideoResult {
  // Existing fields
  id: string;
  videoUrl: string;
  createdAt: number;
  
  // New fields for Quick Create
  processType: 'express' | 'quick-create';
  capcutData?: {
    captionedVideoUrl: string;
    projectBundleUrl: string;
    captionStyle: string;
    processedAt: number;
  };
}
```

#### NEW FILE: Storage Cleanup Policy
```python
# backend/storage_manager.py (TO BE CREATED)
class StorageManager:
    MAX_PROJECTS_PER_USER = 5  # Keep only 5 most recent
    
    def cleanup_old_projects(self, user_id=None):
        """
        Maintain only the 5 most recent projects.
        Older projects are automatically deleted.
        """
        projects_dir = Path(f'/output/{user_id or "default"}')
        
        # Get all project directories sorted by creation time
        projects = sorted(
            projects_dir.glob('*/'),
            key=lambda p: p.stat().st_ctime,
            reverse=True  # Newest first
        )
        
        # Keep only the 5 most recent
        for old_project in projects[self.MAX_PROJECTS_PER_USER:]:
            # Log before deletion
            self.logger.info(f"Deleting old project: {old_project.name}")
            
            # Remove project directory and all contents
            shutil.rmtree(old_project)
            
            # Also remove from cache if exists
            self.remove_from_cache(old_project.name)
    
    def after_project_creation(self, project_id):
        """Called after each new project to trigger cleanup."""
        self.cleanup_old_projects()
        self.logger.info(f"Storage cleanup complete. Kept {self.MAX_PROJECTS_PER_USER} most recent projects")
```

### Phase 12: Implementation Timeline

1. **Week 1**: Backend CapCut automation script
2. **Week 1**: Quick Create frontend page setup
3. **Week 2**: Docker container for server deployment
4. **Week 2**: Integration with existing pipeline
5. **Week 3**: ZIP bundling and project file management
6. **Week 3**: Comprehensive error logging and recovery

### Phase 13: Future Enhancements

1. **Multi-language Support**: Auto-detect and transcribe in different languages
2. **Batch Processing**: Process multiple videos with same caption style
3. **Caption Editing API**: Edit captions programmatically before export
4. **Direct Social Upload**: Push to TikTok/Instagram/YouTube
5. **Caption Analytics**: Track caption readability and engagement

---

## Technical Requirements

### System Requirements

#### Development (Local)
- macOS 11+ or Windows 10+
- CapCut Desktop v3.0+
- Python 3.8+
- 8GB RAM minimum
- 10GB free disk space

#### Production (Hetzner Cloud - Option 1)
- Linux Server: Ubuntu 22.04, 2 vCPU, 4GB RAM (CX21)
- Windows Server: Windows Server 2022, 4 vCPU, 8GB RAM (CPX31)
- Total Cost: €51.56/month (~$56)

### API Keys Required
- Google Gemini API (existing)
- OpenAI Whisper API (existing - for voiceover)
- No additional APIs needed

### File Size Considerations
| Output Type | Express Builder | Quick Create |
|------------|----------------|----------------|
| Compiled Video (with voiceover) | 50-100 MB | 50-100 MB |
| Captioned Video | N/A | 60-120 MB |
| CapCut Project Bundle (ZIP) | N/A | 200-500 MB |
| Total Storage | ~150 MB | ~700 MB |

---

## Success Metrics

### Quick Create Specific
- [ ] CapCut automation success rate > 90%
- [ ] Auto-transcribe accuracy > 95%
- [ ] Total processing < 7 minutes
- [ ] Project file compatibility 100%
- [ ] TikTok style consistency 100%
- [ ] ZIP bundle generation 100% reliable

### User Satisfaction
- [ ] One-click caption application
- [ ] Professional TikTok styling
- [ ] Editable project files
- [ ] No manual timing adjustments needed
- [ ] Clear error messages when failures occur

---

## Required Implementation Tasks

### New Files to Create:
1. **Backend Components**:
   - `backend/capcut_processor.py` - Main CapCut processing logic
   - `backend/capcut_automation/` directory with automation scripts
   - `backend/capcut_docker_runner.py` - Docker container management
   - `backend/capcut_error_handler.py` - Error handling and logging
   - `backend/storage_manager.py` - Project storage management
   - `backend/utils/zip_bundler.py` - ZIP file creation utility

2. **Frontend Components**:
   - `frontend/app/(toolkit)/quick-create/` entire directory
   - `frontend/app/(toolkit)/quick-create/page.tsx` - Main page
   - `frontend/app/(toolkit)/quick-create/components/` - All UI components

3. **Docker Infrastructure**:
   - `docker/Dockerfile.capcut` - CapCut container definition
   - `docker/docker-compose.yml` - Service orchestration
   - `docker/scripts/` - Installation and setup scripts

### Existing Files to Modify:
1. **Backend API** (`backend/app.py`):
   - Add `apply_captions` flag handling
   - Add `caption_style` parameter
   - Integrate CapCut processor after step 10

2. **Frontend Navigation** (`frontend/components/MainSidebar.tsx`):
   - Already has "Quick Create" link - just needs page implementation

## Key Implementation Notes

1. **Backend Continuation**: Quick Create doesn't restart processing - it continues from where Express Builder finishes
2. **Auto-Transcribe Focus**: We're using CapCut's auto-transcribe feature on the audio track (voiceover), not manual caption entry
3. **Server Architecture**: Linux backend server + Windows CapCut server (no Docker/Wine needed)
4. **Single Endpoint**: Both Express Builder and Quick Create use `/api/process` with different flags
5. **ZIP Bundling**: All outputs packaged in a single downloadable ZIP for convenience
6. **Network**: Both servers in same Hetzner datacenter for fast transfers

## Implementation Decisions

### Finalized Approach (Option 1 - Hetzner):
1. **Server Architecture**: Hetzner Linux (backend) + Hetzner Windows (CapCut)
2. **CapCut Automation**: PyAutoGUI on real Windows Server 2022
3. **Caption Style Persistence**: Not needed - user selects each time
4. **Progress Indication**: Simple status messages via SSE
5. **Error Handling**: Screenshots + comprehensive logging
6. **Storage Management**: Keep only 5 most recent projects
7. **Version Pinning**: CapCut v3.9.0 (latest as of Dec 2024)
8. **Monthly Cost**: €51.56 total (~$56)

This architecture provides two distinct but complementary experiences:
- **Express Builder**: Fast video generation with voiceover
- **Quick Create**: Complete solution with auto-transcribed captions

Both use the same backend pipeline, with Quick Create simply continuing where Express Builder completes, adding professional TikTok captions through CapCut's auto-transcribe feature.