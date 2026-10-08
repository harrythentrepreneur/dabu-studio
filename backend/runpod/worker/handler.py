"""
RunPod Serverless Worker Handler for Video Processing
Handles heavy video processing tasks delegated from the lightweight Flask backend
"""

import runpod
import os
import json
import subprocess
import tempfile
import shutil
import boto3
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize S3 client for Digital Ocean Spaces (if needed)
def get_s3_client():
    """Initialize S3 client for Digital Ocean Spaces"""
    if os.getenv("DO_SPACES_KEY") and os.getenv("DO_SPACES_SECRET"):
        return boto3.client(
            's3',
            endpoint_url='https://nyc3.digitaloceanspaces.com',
            aws_access_key_id=os.getenv("DO_SPACES_KEY"),
            aws_secret_access_key=os.getenv("DO_SPACES_SECRET"),
            region_name='nyc3'
        )
    return None

def download_file(url: str, destination: str) -> bool:
    """Download file from URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return False

def upload_to_spaces(file_path: str, object_key: str) -> Optional[str]:
    """Upload file to Digital Ocean Spaces"""
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    try:
        bucket_name = os.getenv("DO_SPACES_BUCKET", "")
        s3_client.upload_file(file_path, bucket_name, object_key)
        return f"https://{bucket_name}.nyc3.digitaloceanspaces.com/{object_key}"
    except Exception as e:
        logger.error(f"Failed to upload to Spaces: {e}")
        return None

def run_ffmpeg_command(command: List[str]) -> tuple[bool, str]:
    """Execute FFmpeg command"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"FFmpeg error: {e.stderr}"

def process_video_merge(videos: List[str], output_path: str) -> bool:
    """Merge multiple videos into one"""
    # Create concat file
    concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    for video in videos:
        concat_file.write(f"file '{video}'\n")
    concat_file.close()
    
    command = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file.name,
        '-c', 'copy',
        output_path
    ]
    
    success, _ = run_ffmpeg_command(command)
    os.unlink(concat_file.name)
    return success

def compress_video(input_path: str, output_path: str, target_size_mb: int = 100) -> bool:
    """Compress video for Gemini processing"""
    command = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', 'scale=480:-2',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-b:v', '1M',
        '-r', '15',
        '-c:a', 'aac',
        '-b:a', '64k',
        output_path
    ]
    
    success, _ = run_ffmpeg_command(command)
    return success

def extract_segment(input_path: str, start_time: float, end_time: float, output_path: str) -> bool:
    """Extract video segment"""
    duration = end_time - start_time
    command = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', input_path,
        '-t', str(duration),
        '-c', 'copy',
        output_path
    ]
    
    success, _ = run_ffmpeg_command(command)
    return success

def add_voiceover(video_path: str, audio_path: str, output_path: str) -> bool:
    """Add voiceover to video"""
    command = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        output_path
    ]
    
    success, _ = run_ffmpeg_command(command)
    return success

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler for RunPod serverless worker
    
    Job input structure:
    {
        "task_type": "merge_videos" | "compress_video" | "extract_segments" | "add_voiceover" | "full_pipeline",
        "request_id": "unique-request-id",
        "inputs": {
            "videos": ["url1", "url2", ...],  # For merge_videos
            "video": "url",                   # For single video operations
            "audio": "url",                    # For voiceover
            "segments": [                      # For extract_segments
                {"start": 0.0, "end": 5.0, "text": "..."},
                ...
            ],
            "script": "...",                   # For full_pipeline
            "duration": 30,                    # Target duration
        }
    }
    """
    try:
        job_input = job.get("input", {})
        task_type = job_input.get("task_type", "full_pipeline")
        request_id = job_input.get("request_id", datetime.now().isoformat())
        inputs = job_input.get("inputs", {})
        
        # Create temporary working directory
        work_dir = tempfile.mkdtemp(prefix=f"runpod_{request_id}_")
        logger.info(f"Processing {task_type} for request {request_id}")
        
        result = {"status": "error", "message": "Unknown task type"}
        
        try:
            if task_type == "merge_videos":
                # Download all videos
                video_paths = []
                for i, video_url in enumerate(inputs.get("videos", [])):
                    video_path = os.path.join(work_dir, f"video_{i}.mp4")
                    if download_file(video_url, video_path):
                        video_paths.append(video_path)
                
                # Merge videos
                merged_path = os.path.join(work_dir, "merged.mp4")
                if process_video_merge(video_paths, merged_path):
                    # Upload result
                    url = upload_to_spaces(merged_path, f"{request_id}/merged.mp4")
                    result = {
                        "status": "success",
                        "output_url": url or "local",
                        "file_size": os.path.getsize(merged_path)
                    }
                
            elif task_type == "compress_video":
                # Download video
                video_path = os.path.join(work_dir, "input.mp4")
                if download_file(inputs.get("video"), video_path):
                    # Compress
                    compressed_path = os.path.join(work_dir, "compressed.mp4")
                    if compress_video(video_path, compressed_path):
                        # Upload result
                        url = upload_to_spaces(compressed_path, f"{request_id}/compressed.mp4")
                        result = {
                            "status": "success",
                            "output_url": url or "local",
                            "file_size": os.path.getsize(compressed_path),
                            "compression_ratio": os.path.getsize(video_path) / os.path.getsize(compressed_path)
                        }
            
            elif task_type == "extract_segments":
                # Download source video
                video_path = os.path.join(work_dir, "source.mp4")
                if download_file(inputs.get("video"), video_path):
                    segments = inputs.get("segments", [])
                    extracted = []
                    
                    for i, segment in enumerate(segments):
                        segment_path = os.path.join(work_dir, f"segment_{i}.mp4")
                        if extract_segment(video_path, segment["start"], segment["end"], segment_path):
                            # Upload segment
                            url = upload_to_spaces(segment_path, f"{request_id}/segment_{i}.mp4")
                            extracted.append({
                                "index": i,
                                "url": url or "local",
                                "start": segment["start"],
                                "end": segment["end"],
                                "text": segment.get("text", "")
                            })
                    
                    # Merge all segments into final video
                    if extracted:
                        segment_paths = [os.path.join(work_dir, f"segment_{i}.mp4") for i in range(len(segments))]
                        final_path = os.path.join(work_dir, "final.mp4")
                        if process_video_merge(segment_paths, final_path):
                            final_url = upload_to_spaces(final_path, f"{request_id}/final.mp4")
                            result = {
                                "status": "success",
                                "segments": extracted,
                                "final_video_url": final_url or "local"
                            }
            
            elif task_type == "add_voiceover":
                # Download video and audio
                video_path = os.path.join(work_dir, "video.mp4")
                audio_path = os.path.join(work_dir, "audio.mp3")
                
                if download_file(inputs.get("video"), video_path) and \
                   download_file(inputs.get("audio"), audio_path):
                    # Add voiceover
                    output_path = os.path.join(work_dir, "with_voiceover.mp4")
                    if add_voiceover(video_path, audio_path, output_path):
                        # Upload result
                        url = upload_to_spaces(output_path, f"{request_id}/with_voiceover.mp4")
                        result = {
                            "status": "success",
                            "output_url": url or "local"
                        }
            
            elif task_type == "full_pipeline":
                # This would implement the complete pipeline
                # For now, return a placeholder
                result = {
                    "status": "success",
                    "message": "Full pipeline would be implemented here",
                    "steps": [
                        "1. Merge videos",
                        "2. Compress for Gemini",
                        "3. Analyze with Gemini API",
                        "4. Extract segments",
                        "5. Add voiceover if provided",
                        "6. Upload final result"
                    ]
                }
                
        finally:
            # Cleanup
            shutil.rmtree(work_dir, ignore_errors=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# RunPod serverless worker entry point
runpod.serverless.start({"handler": handler})