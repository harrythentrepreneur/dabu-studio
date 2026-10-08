"""
RunPod Serverless Handler for CapCut Web Automation
Entry point for RunPod serverless GPU/CPU instances
"""

import os
import sys
import json
import time
import asyncio
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/app')

import runpod
import sys
from pathlib import Path

# Ensure the official RunPod SDK submodules (e.g. runpod.serverless) are discoverable
try:
    import pkg_resources  # Part of setuptools
    dist = pkg_resources.get_distribution("runpod")
    sdk_pkg_path = Path(dist.location) / "runpod"
    if sdk_pkg_path.exists() and str(sdk_pkg_path) not in runpod.__path__:
        runpod.__path__.append(str(sdk_pkg_path))
except Exception:
    # Best-effort; if this fails, an AttributeError on serverless import will surface clearly
    pass

# Explicitly import the SDK submodule to avoid relying on package-level magic
from runpod import serverless as rp_serverless
from utils.logger import get_logger
from services.cloud_storage_service import CloudStorageService

# Initialize logger
logger = get_logger(__name__)

# Initialize services
storage_service = None
orchestrator = None  # Intentionally left None; browser automation is disabled for now


def initialize_services():
    """Initialize services on cold start"""
    global storage_service, orchestrator
    
    try:
        # Initialize cloud storage only (no browser automation)
        storage_service = CloudStorageService()
        logger.info("Cloud storage service initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False


def download_video_from_url(video_url: str) -> str:
    """
    Download video from URL to local temp file
    
    Args:
        video_url: URL of the video to download
        
    Returns:
        Local path to downloaded video
    """
    import requests
    
    # Create temp file
    temp_dir = tempfile.mkdtemp(prefix="runpod_video_")
    video_path = os.path.join(temp_dir, "input_video.mp4")
    
    try:
        # Download video
        logger.info(f"Downloading video from {video_url}")
        response = requests.get(video_url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Save to file
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Video downloaded to {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"Failed to download video: {e}")
        raise


def upload_result_to_storage(local_path: str, request_id: str) -> str:
    """
    Upload processed video to cloud storage
    
    Args:
        local_path: Local path to the processed video
        request_id: Request ID for naming
        
    Returns:
        URL of uploaded video
    """
    global storage_service
    
    if not storage_service:
        raise Exception("Storage service not initialized")
        
    try:
        # Upload to cloud storage
        filename = f"capcut_output/{request_id}/captioned_video.mp4"
        url = storage_service.upload_file(local_path, filename)
        logger.info(f"Uploaded result to {url}")
        return url
        
    except Exception as e:
        logger.error(f"Failed to upload result: {e}")
        raise


async def process_video_async(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video asynchronously
    
    Args:
        job_input: Input parameters from RunPod
        
    Returns:
        Processing result
    """
    global orchestrator, storage_service
    
    video_paths = []
    voiceover_path = None
    temp_dirs = []
    
    try:
        # Extract parameters - handle new structure from Next.js
        request_id = job_input.get('request_id', f"runpod_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        task_type = job_input.get('task_type', 'express_builder')
        script = job_input.get('script', '')
        videos = job_input.get('videos', [])  # Array of video URLs
        voiceover = job_input.get('voiceover')  # Optional voiceover URL
        duration = job_input.get('duration', 30)
        
        # Backward compatibility for old format
        if not videos and job_input.get('video_url'):
            videos = [job_input.get('video_url')]
        
        if not videos:
            raise ValueError("No video URLs provided")
            
        logger.info(f"Processing {task_type} request {request_id} with {len(videos)} videos")
        
        # Download all videos from URLs (Digital Ocean Spaces)
        for i, video_url in enumerate(videos):
            logger.info(f"Downloading video {i+1}/{len(videos)}: {video_url}")
            video_path = download_video_from_url(video_url)
            video_paths.append(video_path)
            temp_dirs.append(Path(video_path).parent)
        
        # Download voiceover if provided
        if voiceover:
            logger.info(f"Downloading voiceover: {voiceover}")
            voiceover_path = download_video_from_url(voiceover)  # Works for audio too
            temp_dirs.append(Path(voiceover_path).parent)
            
        logger.info(f"Processing {task_type} for request {request_id}")
        
        # Based on task type, run different processing pipelines
        if task_type in ('express_builder', 'quick_create', 'full_pipeline'):
            # Import the business logic from main backend
            from business import PipelineOrchestrator
            from pathlib import Path
            
            # Create temp directory for outputs
            output_dir = Path(tempfile.mkdtemp(prefix=f"runpod_output_{request_id}_"))
            
            # Initialize pipeline orchestrator (expects temp_dir, output_dir)
            pipeline = PipelineOrchestrator(
                temp_dir=Path(temp_dirs[0]) if temp_dirs else Path('/tmp'),
                output_dir=output_dir
            )
            
            # Process the videos with script
            result = await pipeline.process_async(
                script=script,
                video_paths=video_paths,
                voiceover_path=voiceover_path,
                target_duration=duration,
                request_id=request_id,
                processing_mode=task_type
            )
            
            # Upload all output files to DO Spaces and return URLs
            output_urls = {}
            
            if result.get('success'):
                # Upload main video
                if result.get('video_path') and Path(result['video_path']).exists():
                    video_url = storage_service.upload_file(
                        result['video_path'],
                        f"outputs/{request_id}/compiled_video.mp4",
                        public=True
                    )
                    output_urls['videoUrl'] = video_url
                
                # Upload script
                if result.get('script_path') and Path(result['script_path']).exists():
                    script_url = storage_service.upload_file(
                        result['script_path'],
                        f"outputs/{request_id}/script.txt",
                        public=True
                    )
                    output_urls['scriptUrl'] = script_url
                
                # Upload timestamps
                if result.get('timestamps_path') and Path(result['timestamps_path']).exists():
                    timestamps_url = storage_service.upload_file(
                        result['timestamps_path'],
                        f"outputs/{request_id}/timestamps.json",
                        public=True
                    )
                    output_urls['timestampsUrl'] = timestamps_url
                
                # Upload captioned video if available
                if result.get('captioned_video_path') and Path(result['captioned_video_path']).exists():
                    captioned_url = storage_service.upload_file(
                        result['captioned_video_path'],
                        f"outputs/{request_id}/captioned_video.mp4",
                        public=True
                    )
                    output_urls['captionedVideoUrl'] = captioned_url
                
                # Upload project bundle if available
                if result.get('project_bundle_path') and Path(result['project_bundle_path']).exists():
                    bundle_url = storage_service.upload_file(
                        result['project_bundle_path'],
                        f"outputs/{request_id}/project_bundle.zip",
                        public=True
                    )
                    output_urls['projectBundleUrl'] = bundle_url
                
                return {
                    'success': True,
                    'request_id': request_id,
                    **output_urls,
                    'segments': result.get('segments', []),
                    'processingMode': task_type,
                    'capcutSuccess': result.get('capcut_success', False),
                    'processing_time': result.get('processing_time', 0)
                }
            else:
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': result.get('error', 'Processing failed'),
                    'processing_time': result.get('processing_time', 0)
                }
            
        else:
            # Handle other task types if needed
            return {
                'success': False,
                'request_id': request_id,
                'error': f'Unknown task type: {task_type}'
            }
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
    finally:
        # Cleanup all temp directories
        for temp_dir in temp_dirs:
            if temp_dir and Path(temp_dir).exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")


# Defer serverless.start until after handler is defined to avoid NameError

# Local testing mode (defer starting serverless until after handler is defined)
if __name__ == "__main__":
    run_local_test = False
    run_local_api = False
    if '--test' in sys.argv:
        # Test mode - run a sample job
        logger.info("Running in test mode")
        os.environ['LOCAL_TESTING'] = '1'
        
        # Initialize services
        initialize_services()
        
        # Test job
        test_job = {
            'id': 'test_job_001',
            'input': {
                'type': 'health_check'
            }
        }
        
        # Note: handler is defined below; we will invoke directly here by
        # importing via globals after definition if needed. For now, set a flag.
        run_local_test = True
        os.environ['RUN_LOCAL_TEST_JOB_PAYLOAD'] = json.dumps(test_job)
        
    elif '--rp_serve_api' in sys.argv:
        # RunPod local API server mode
        logger.info("Deferring RunPod local API server start until handler is defined")
        os.environ['LOCAL_TESTING'] = '1'
        run_local_api = True

# RunPod serverless entry point - this is what RunPod calls
def handler(job):
    """
    RunPod serverless handler function - this is the entry point RunPod expects
    
    Args:
        job: RunPod job object with input data
        
    Returns:
        Job result that RunPod will send back
    """
    try:
        # Initialize services if not already done
        if not orchestrator:
            if not initialize_services():
                return {
                    'success': False,
                    'error': 'Failed to initialize services'
                }
        
        # Process the job using our existing handler logic
        return handler_internal(job)
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

def handler_internal(job):
    """
    Internal handler logic - renamed from original handler function
    """
    try:
        job_input = job.get('input', {})
        # Normalize input schema: merge nested 'inputs' into top-level
        # Support both {'type': ..., 'videos': [...]} and
        # {'task_type': ..., 'inputs': {'videos': [...], 'script': ...}}
        nested_inputs = job_input.get('inputs') or {}
        if isinstance(nested_inputs, dict):
            # Only set if not already present at top-level
            for key in ['videos', 'video', 'audio', 'voiceover', 'segments', 'script', 'duration']:
                job_input.setdefault(key, nested_inputs.get(key))
        
        # Log job details
        logger.info(f"Received job: {job.get('id')}")
        logger.info(f"Input type: {job_input.get('type', 'process_video')}")
        
        # Handle different job types
        job_type = job_input.get('type') or job_input.get('task_type') or 'process_video'
        
        if job_type == 'health_check':
            # Simple health check
            stats = {}
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'stats': stats
            }
            
        elif job_type == 'process_video':
            # Process video with captions
            
            # Initialize services if not already done
            if not orchestrator:
                if not initialize_services():
                    return {
                        'success': False,
                        'error': 'Failed to initialize services'
                    }
                    
            # Run async processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    process_video_async(job_input)
                )
                return result
            finally:
                loop.close()
                
        elif job_type == 'get_status':
            # Get status of a specific request
            request_id = job_input.get('request_id')
            if not request_id:
                return {
                    'success': False,
                    'error': 'request_id is required'
                }
                
            status = None
            return {
                'success': True,
                'status': status
            }
            
        elif job_type == 'get_stats':
            # Get orchestrator statistics
            stats = {}
            return {
                'success': True,
                'stats': stats
            }
            
        else:
            return {
                'success': False,
                'error': f'Unknown job type: {job_type}'
            }
            
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


# Initialize services and start serverless AFTER handler is defined
if not os.getenv('LOCAL_TESTING'):
    logger.info("Initializing services for RunPod serverless")
    initialize_services()
    rp_serverless.start({
        "handler": handler,
        "return_aggregate_stream": True
    })

# Start local API after handler is defined if requested
if __name__ == "__main__" and run_local_api:
    initialize_services()
    rp_serverless.start({
        "handler": handler
    })

# Run local test job if requested (after handler exists)
if __name__ == "__main__" and run_local_test:
    payload = os.getenv('RUN_LOCAL_TEST_JOB_PAYLOAD')
    if payload:
        try:
            job = json.loads(payload)
            print(json.dumps(handler(job), indent=2))
        except Exception as _e:
            logger.error(f"Local test job failed: {_e}")