"""
Express Builder Handler for RunPod
Processes videos using Gemini AI for script-to-video alignment
"""

import runpod
import os
import json
import subprocess
import tempfile
import shutil
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests
import boto3
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Gemini client
import google.generativeai as genai

class ExpressBuilderProcessor:
    """Express Builder processing logic for RunPod"""
    
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Initialize S3 client for Digital Ocean Spaces
        self.s3_client = None
        if os.getenv("DO_SPACES_KEY") and os.getenv("DO_SPACES_SECRET"):
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{os.getenv("DO_SPACES_REGION", "sfo3")}.digitaloceanspaces.com',
                aws_access_key_id=os.getenv("DO_SPACES_KEY"),
                aws_secret_access_key=os.getenv("DO_SPACES_SECRET"),
                region_name=os.getenv("DO_SPACES_REGION", "sfo3")
            )
            self.bucket_name = os.getenv("DO_SPACES_BUCKET", "")
            logger.info(f"Initialized DO Spaces client for bucket: {self.bucket_name}")
    
    def download_file(self, url: str, destination: str) -> bool:
        """Download file from URL"""
        try:
            logger.info(f"Downloading {url} to {destination}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded {os.path.getsize(destination)} bytes")
            return True
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def upload_to_spaces(self, file_path: str, object_key: str) -> Optional[str]:
        """Upload file to Digital Ocean Spaces"""
        if not self.s3_client:
            logger.warning("S3 client not initialized, skipping upload")
            return None
        
        try:
            logger.info(f"Uploading {file_path} to {self.bucket_name}/{object_key}")
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                object_key,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            url = f"https://{self.bucket_name}.{os.getenv('DO_SPACES_REGION', 'sfo3')}.digitaloceanspaces.com/{object_key}"
            logger.info(f"Uploaded to: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to upload to Spaces: {e}")
            return None
    
    def merge_videos_ffmpeg(self, video_paths: List[str], output_path: str) -> bool:
        """Merge multiple videos using FFmpeg - supports both local files and URLs"""
        try:
            # Check if we're dealing with URLs or local files
            are_urls = all(path.startswith('http') for path in video_paths)
            
            if False:  # Disabled filter_complex for now - concat demuxer works better
                # For a few URLs (<=5), use filter_complex concat
                # More than 5 URLs with filter_complex is too slow/memory intensive
                logger.info(f"Merging {len(video_paths)} URLs using filter_complex")
                
                # Build input list
                inputs = []
                for url in video_paths:
                    inputs.extend(['-i', url])
                
                # Build filter complex string with scaling
                filter_parts = []
                for i in range(len(video_paths)):
                    # Scale each input to 1080x1920 before concatenating
                    filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v{i}];")
                
                # Build the concat part
                video_inputs = "".join([f"[v{i}]" for i in range(len(video_paths))])
                audio_inputs = "".join([f"[{i}:a]" for i in range(len(video_paths))])
                filter_str = "".join(filter_parts) + f"{video_inputs}{audio_inputs}concat=n={len(video_paths)}:v=1:a=1[outv][outa]"
                
                cmd = ['ffmpeg', '-y'] + inputs + [
                    '-filter_complex', filter_str,
                    '-map', '[outv]',
                    '-map', '[outa]',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    output_path
                ]
            else:
                # For local files or single URL, use concat demuxer
                concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                for video in video_paths:
                    concat_file.write(f"file '{video}'\n")
                concat_file.close()
                
                cmd = ['ffmpeg', '-y']
                
                if are_urls:
                    # For URLs, use protocol whitelist and increase buffer size
                    cmd.extend([
                        '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', concat_file.name,
                        '-max_muxing_queue_size', '9999',  # Increase buffer for network streams
                        '-threads', '4'  # Use multiple threads
                    ])
                else:
                    cmd.extend([
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', concat_file.name
                    ])
                
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black',
                    output_path
                ])
            
            logger.info(f"Running FFmpeg merge command with {len(video_paths)} inputs")
            if are_urls:
                logger.info(f"Concat file content:\n{open(concat_file.name).read()}")
            logger.debug(f"FFmpeg command: {' '.join(cmd[:50])}...")  # Log first part of command
            
            # For many URLs, this can take a while
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if 'concat_file' in locals():
                os.unlink(concat_file.name)
            
            if result.returncode == 0:
                # Check output file size to verify merge worked
                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"Successfully merged {len(video_paths)} videos. Output size: {output_size_mb:.2f} MB")
                
                # Get video duration to verify
                duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                               '-of', 'default=noprint_wrappers=1:nokey=1', output_path]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                if duration_result.returncode == 0:
                    duration = float(duration_result.stdout.strip())
                    logger.info(f"Merged video duration: {duration:.2f} seconds")
                
                return True
            else:
                logger.error(f"FFmpeg merge failed: {result.stderr[:500]}")  # Limit error log size
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg merge timed out after 20 minutes")
            return False
        except Exception as e:
            logger.error(f"Error merging videos: {e}")
            return False
    
    def compress_for_gemini(self, input_source: str, output_path: str) -> bool:
        """Compress video for Gemini API (< 100MB) - works with URLs or local files"""
        try:
            is_url = input_source.startswith('http')
            
            cmd = ['ffmpeg', '-y']
            
            # For URLs, add input seeking and protocol support
            if is_url:
                logger.info("Compressing directly from URL")
                cmd.extend([
                    '-protocol_whitelist', 'file,http,https,tcp,tls',
                    '-i', input_source
                ])
            else:
                cmd.extend(['-i', input_source])
            
            # Compression settings for <100MB output
            cmd.extend([
                '-vf', 'scale=480:-2',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-b:v', '1M',
                '-r', '15',
                '-c:a', 'aac',
                '-b:a', '64k',
                '-movflags', '+faststart',  # Optimize for streaming
                output_path
            ])
            
            logger.info(f"Compressing {'URL' if is_url else 'file'} for Gemini...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode == 0:
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"Compressed video to {size_mb:.2f} MB")
                return True
            else:
                logger.error(f"Compression failed: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Compression timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"Error compressing video: {e}")
            return False
    
    def analyze_with_gemini(self, video_url_or_path: str, script: str, target_duration: int) -> Dict[str, Any]:
        """Analyze video with Gemini to match script segments
        
        Args:
            video_url_or_path: Either a URL (DO Spaces) or local file path
            script: Script text to match
            target_duration: Target duration in seconds
        """
        try:
            logger.info("Starting Gemini analysis")
            
            # We need the video as a local file for Gemini File API
            if video_url_or_path.startswith('http'):
                # Download from URL for Gemini analysis
                logger.info(f"Downloading video from URL for Gemini analysis: {video_url_or_path}")
                import tempfile
                temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_video_path = temp_video.name
                temp_video.close()
                
                if not self.download_file(video_url_or_path, temp_video_path):
                    raise Exception("Failed to download video for Gemini analysis")
                
                # Check file size
                file_size_mb = os.path.getsize(temp_video_path) / (1024 * 1024)
                logger.info(f"Downloaded video for Gemini: {file_size_mb:.2f} MB")
                
                video_path = temp_video_path
                cleanup_needed = True
            else:
                # Local file
                logger.info(f"Using local file for Gemini: {video_url_or_path}")
                video_path = video_url_or_path
                cleanup_needed = False
            
            # Upload to Gemini File API
            logger.info("Uploading video to Gemini File API")
            video_file = genai.upload_file(path=video_path, display_name="video_analysis")
            
            # Wait for file to be processed
            logger.info("Waiting for Gemini to process video...")
            import time
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise Exception(f"Gemini file processing failed: {video_file.state.name}")
            
            logger.info(f"Video ready for analysis: {video_file.uri}")
            
            # Create prompt for Gemini with the uploaded video
            prompt = f"""
            Analyze this video and match the following script segments to appropriate timestamps.
            
            Script (target duration: {target_duration} seconds):
            {script}
            
            For each line/segment of the script:
            1. Find the best matching video timestamp
            2. Describe WHY this visual moment matches the script
            3. Provide a confidence score (0.0-1.0)
            
            Return a JSON object with this structure:
            {{
                "segments": [
                    {{
                        "text": "script line",
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "visual_description": "Detailed description of what's happening in the video at this moment and why it matches",
                        "confidence": 0.95
                    }}
                ]
            }}
            
            Be specific in your visual descriptions - explain the visual elements, actions, emotions, or scenes that make this timestamp appropriate for the script segment.
            
            Ensure the total duration is approximately {target_duration} seconds.
            """
            
            # Generate response with the uploaded video file
            response = self.model.generate_content([video_file, prompt])
            
            # Parse JSON from response
            text = response.text
            # Extract JSON from response (handle markdown code blocks)
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            result = json.loads(text.strip())
            logger.info(f"Gemini analysis complete: {len(result.get('segments', []))} segments")
            
            # Cleanup temporary file if needed
            if cleanup_needed and os.path.exists(video_path):
                os.remove(video_path)
                logger.info("Cleaned up temporary video file")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            # Cleanup on error
            if 'cleanup_needed' in locals() and cleanup_needed and 'video_path' in locals() and os.path.exists(video_path):
                os.remove(video_path)
            return {"segments": []}
    
    def extract_segments(self, video_source: str, segments: List[Dict], output_dir: str) -> List[str]:
        """Extract video segments using FFmpeg - supports both local files and URLs"""
        segment_paths = []
        is_url = video_source.startswith('http')
        
        for i, segment in enumerate(segments):
            output_path = os.path.join(output_dir, f"segment_{i:03d}.mp4")
            duration = segment['end_time'] - segment['start_time']
            
            # Build FFmpeg command
            cmd = ['ffmpeg', '-y']
            
            # For URLs, use input seeking for efficiency
            if is_url:
                # Input seek (faster for HTTP sources)
                cmd.extend([
                    '-ss', str(segment['start_time']),
                    '-t', str(duration),
                    '-i', video_source
                ])
            else:
                # Output seek (more accurate for local files)
                cmd.extend([
                    '-i', video_source,
                    '-ss', str(segment['start_time']),
                    '-t', str(duration)
                ])
            
            # Output options
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                output_path
            ])
            
            logger.info(f"Extracting segment {i} ({duration:.1f}s) from {'URL' if is_url else 'file'}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # 2 min per segment
            
            if result.returncode == 0:
                segment_paths.append(output_path)
                logger.info(f"Extracted segment {i}: {segment.get('text', '')[:30]}...")
            else:
                logger.error(f"Failed to extract segment {i}: {result.stderr[:200]}")
        
        return segment_paths
    
    def process_express_builder(self, job_input: Dict[str, Any]) -> Dict[str, Any]:
        """Main Express Builder processing pipeline - optimized for DO Spaces"""
        request_id = job_input.get('request_id', datetime.now().isoformat())
        work_dir = tempfile.mkdtemp(prefix=f"express_{request_id}_")
        
        try:
            logger.info(f"Processing Express Builder request {request_id}")
            
            # Extract inputs
            script = job_input.get('script', '')
            video_urls = job_input.get('videos', [])
            target_duration = job_input.get('target_duration', 30)
            voiceover_url = job_input.get('voiceover')
            
            # Initialize variables to avoid scope issues
            merged_path = None
            merged_url = None
            
            # Check if videos are already in DO Spaces
            videos_in_spaces = all(url.startswith('http') for url in video_urls)
            
            if videos_in_spaces and len(video_urls) == 1:
                # OPTIMIZATION: Single video already in DO Spaces
                # Pass URL directly to Gemini (no download needed!)
                logger.info("Single video in DO Spaces - using direct URL for Gemini")
                
                video_url = video_urls[0]
                
                # Use DO Spaces URL directly with Gemini (no download!)
                merged_url = video_url
                
                # We'll need to download for segment extraction later
                # But defer that until after Gemini analysis
                merged_path = None  # Will download later if needed
                
            elif videos_in_spaces:
                # For multiple videos in DO Spaces - download then merge
                # FFmpeg concat with URLs is unreliable for many files
                logger.info(f"Processing {len(video_urls)} videos from DO Spaces")
                
                # Download videos in parallel for speed
                import concurrent.futures
                video_paths = []
                
                def download_video(args):
                    i, url = args
                    video_path = os.path.join(work_dir, f"input_video_{i:03d}.mp4")
                    logger.info(f"Downloading video {i+1}/{len(video_urls)}")
                    if self.download_file(url, video_path):
                        return video_path
                    return None
                
                # Download in parallel with thread pool
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures = executor.map(download_video, enumerate(video_urls))
                    video_paths = [path for path in futures if path]
                
                if len(video_paths) != len(video_urls):
                    raise Exception(f"Failed to download all videos. Got {len(video_paths)}/{len(video_urls)}")
                
                logger.info(f"Downloaded all {len(video_paths)} videos, now merging")
                
                # Merge the downloaded files locally (reliable)
                merged_path = os.path.join(work_dir, "merged.mp4")
                if not self.merge_videos_ffmpeg(video_paths, merged_path):
                    raise Exception("Failed to merge videos")
                
                # Upload merged video to DO Spaces for URL-based compression
                if self.s3_client and merged_path and os.path.exists(merged_path):
                    merged_key = f"temp/{request_id}/merged_full.mp4"
                    merged_url = self.upload_to_spaces(merged_path, merged_key)
                    if merged_url:
                        logger.info(f"Uploaded merged video to: {merged_url}")
                        # Now we can delete local merged file and use URL
                        os.remove(merged_path)
                        merged_path = None  # Use URL from now on
                    else:
                        merged_url = merged_path  # Fallback to local file
            else:
                # Local files - need to download and merge
                logger.info(f"Processing {len(video_urls)} videos - downloading for merge")
                
                # Step 1: Download videos
                video_paths = []
                for i, url in enumerate(video_urls):
                    video_path = os.path.join(work_dir, f"input_video_{i}.mp4")
                    if self.download_file(url, video_path):
                        video_paths.append(video_path)
                    else:
                        raise Exception(f"Failed to download video {i}")
                
                # Step 2: Merge videos
                logger.info(f"Starting merge of {len(video_paths)} videos")
                total_size = sum(os.path.getsize(p) for p in video_paths) / (1024*1024)
                logger.info(f"Total input size: {total_size:.2f} MB")
                
                merged_path = os.path.join(work_dir, "merged.mp4")
                if not self.merge_videos_ffmpeg(video_paths, merged_path):
                    raise Exception("Failed to merge videos")
                logger.info(f"Merged video created: {os.path.getsize(merged_path) / (1024*1024):.2f} MB")
                
                # Step 3: Compress for Gemini (try from URL if available)
                logger.info("Starting compression for Gemini")
                compressed_path = os.path.join(work_dir, "compressed.mp4")
                
                # Check if we should compress from URL or local file
                compress_source = merged_url if merged_url else merged_path
                if not compress_source:
                    raise Exception("No video source available for compression")
                
                if not self.compress_for_gemini(compress_source, compressed_path):
                    raise Exception("Failed to compress video")
                logger.info(f"Compressed video: {os.path.getsize(compressed_path) / (1024*1024):.2f} MB")
                
                # Step 3.5: Upload compressed to DO Spaces for Gemini
                compressed_key = f"temp/{request_id}/compressed_gemini.mp4"
                compressed_url = self.upload_to_spaces(compressed_path, compressed_key)
                merged_url = compressed_url or compressed_path
            
            # Step 4: Analyze with Gemini (using DO Spaces URL if available)
            logger.info(f"Starting Gemini analysis with target duration: {target_duration}s")
            analysis = self.analyze_with_gemini(merged_url, script, target_duration)
            segments = analysis.get('segments', [])
            
            if not segments:
                raise Exception("Gemini analysis returned no segments")
            logger.info(f"Gemini returned {len(segments)} segments")
            
            # Step 5: Extract segments (try to use URL directly if available)
            segments_dir = os.path.join(work_dir, "segments")
            os.makedirs(segments_dir, exist_ok=True)
            
            # Determine source for extraction
            extract_source = merged_url if merged_url else merged_path
            if not extract_source:
                raise Exception("No video source available for segment extraction")
            
            logger.info(f"Extracting {len(segments)} segments from {'URL' if extract_source.startswith('http') else 'local file'}")
            
            # Try extraction directly from URL first
            segment_paths = self.extract_segments(extract_source, segments, segments_dir)
            
            # If URL extraction failed and we haven't downloaded yet, download and retry
            if not segment_paths and extract_source.startswith('http'):
                logger.warning("URL extraction failed, downloading video for local extraction")
                merged_path = os.path.join(work_dir, "video_for_extraction.mp4")
                if self.download_file(extract_source, merged_path):
                    segment_paths = self.extract_segments(merged_path, segments, segments_dir)
                else:
                    raise Exception("Failed to download video for extraction")
            logger.info(f"Successfully extracted {len(segment_paths)} segments")
            
            # Step 6: Merge segments into final video
            logger.info("Creating final video from segments")
            final_path = os.path.join(work_dir, "final_output.mp4")
            if not self.merge_videos_ffmpeg(segment_paths, final_path):
                raise Exception("Failed to create final video")
            logger.info(f"Final video created: {os.path.getsize(final_path) / (1024*1024):.2f} MB")
            
            # Step 7: Add voiceover if provided
            if voiceover_url:
                voiceover_path = os.path.join(work_dir, "voiceover.mp3")
                if self.download_file(voiceover_url, voiceover_path):
                    final_with_audio = os.path.join(work_dir, "final_with_voiceover.mp4")
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', final_path,
                        '-i', voiceover_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        final_with_audio
                    ]
                    if subprocess.run(cmd, capture_output=True).returncode == 0:
                        final_path = final_with_audio
            
            # Step 8: Upload results to Digital Ocean
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Upload final video
            video_key = f"outputs/{request_id}/compiled_video_{timestamp}.mp4"
            video_url = self.upload_to_spaces(final_path, video_key)
            
            # Save and upload script
            script_path = os.path.join(work_dir, "script.txt")
            with open(script_path, 'w') as f:
                f.write(script)
            script_key = f"outputs/{request_id}/script_{timestamp}.txt"
            script_url = self.upload_to_spaces(script_path, script_key)
            
            # Save and upload timestamps - convert to expected format
            timestamps_path = os.path.join(work_dir, "timestamps.json")
            
            # Convert segments to script_segments format for compatibility
            timestamps_data = {
                "script_segments": [],
                "total_duration": target_duration,
                "target_duration": target_duration
            }
            
            for i, segment in enumerate(analysis.get('segments', []), 1):
                start_time = segment.get('start_time', 0)
                end_time = segment.get('end_time', 0)
                
                # Format timestamps properly (handle minutes and seconds)
                start_mins = int(start_time // 60)
                start_secs = start_time % 60
                end_mins = int(end_time // 60)
                end_secs = end_time % 60
                
                # Use actual Gemini response values for visual description and confidence
                timestamps_data["script_segments"].append({
                    "segment_number": i,
                    "segment_text": segment.get('text', ''),
                    "start_timestamp": f"00:{start_mins:02d}:{start_secs:06.3f}",
                    "end_timestamp": f"00:{end_mins:02d}:{end_secs:06.3f}",
                    "duration_seconds": end_time - start_time,
                    "confidence": segment.get('confidence', 0.95),  # Use actual confidence from Gemini
                    "visual_description": segment.get('visual_description', f"Scene segment {i} - AI matched visual content")  # Use actual description
                })
            
            with open(timestamps_path, 'w') as f:
                json.dump(timestamps_data, f, indent=2)
            timestamps_key = f"outputs/{request_id}/timestamps_{timestamp}.json"
            timestamps_url = self.upload_to_spaces(timestamps_path, timestamps_key)
            
            # Return success result
            return {
                "status": "success",
                "request_id": request_id,
                "output": {
                    "final_video_url": video_url or final_path,
                    "script_url": script_url or script_path,
                    "timestamps_url": timestamps_url or timestamps_path,
                    "segments": segments,
                    "duration": target_duration
                }
            }
            
        except Exception as e:
            logger.error(f"Express Builder processing failed: {e}")
            return {
                "status": "error",
                "request_id": request_id,
                "error": str(e)
            }
        finally:
            # Cleanup
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)

# Initialize processor
processor = ExpressBuilderProcessor()

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler for Express Builder
    """
    job_input = job.get("input", {})
    task_type = job_input.get("task_type", "express_builder")
    
    logger.info(f"Received job: {task_type}")
    
    if task_type == "express_builder" or task_type == "full_pipeline":
        return processor.process_express_builder(job_input)
    else:
        return {
            "status": "error",
            "error": f"Unknown task type: {task_type}"
        }

# RunPod serverless entry point
# CRITICAL: This must be at module level, not inside if __name__ == "__main__"
# Otherwise RunPod won't be able to start the handler when importing the module
runpod.serverless.start({"handler": handler})