"""
RunPod API Client for Flask Backend
Handles communication with RunPod serverless workers
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
import requests
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """RunPod job status states"""
    IN_QUEUE = "IN_QUEUE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"

@dataclass
class RunPodConfig:
    """RunPod configuration"""
    api_key: str
    endpoint_id: str
    base_url: str = "https://api.runpod.ai/v2"
    timeout: int = 300  # 5 minutes default
    poll_interval: int = 2  # Poll every 2 seconds

class RunPodClient:
    """Client for interacting with RunPod serverless API"""
    
    def __init__(self, config: Optional[RunPodConfig] = None):
        """Initialize RunPod client"""
        if config:
            self.config = config
        else:
            # Load from environment
            self.config = RunPodConfig(
                api_key=os.getenv("RUNPOD_API_KEY", ""),
                endpoint_id=os.getenv("RUNPOD_ENDPOINT_ID", ""),
                base_url=os.getenv("RUNPOD_BASE_URL", "https://api.runpod.ai/v2"),
                timeout=int(os.getenv("RUNPOD_TIMEOUT", "300")),
                poll_interval=int(os.getenv("RUNPOD_POLL_INTERVAL", "2"))
            )
        
        if not self.config.api_key or not self.config.endpoint_id:
            logger.warning("RunPod API key or endpoint ID not configured")
        
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
    
    def submit_job(self, job_input: Dict[str, Any]) -> Optional[str]:
        """
        Submit a job to RunPod endpoint
        
        Args:
            job_input: Job input data
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            url = f"{self.config.base_url}/{self.config.endpoint_id}/run"
            
            payload = {
                "input": job_input,
                "webhook": os.getenv("RUNPOD_WEBHOOK_URL")  # Optional webhook
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("id")
                logger.info(f"Submitted RunPod job: {job_id}")
                return job_id
            else:
                logger.error(f"Failed to submit job: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting RunPod job: {e}")
            return None
    
    def submit_sync_job(self, job_input: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Submit a synchronous job to RunPod (waits for completion)
        
        Args:
            job_input: Job input data
            timeout: Optional timeout override
            
        Returns:
            Job result
        """
        try:
            url = f"{self.config.base_url}/{self.config.endpoint_id}/runsync"
            
            payload = {
                "input": job_input,
                "timeout": timeout or self.config.timeout
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout or self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "output": result.get("output", {}),
                    "job_id": result.get("id")
                }
            else:
                return {
                    "status": "error",
                    "message": f"RunPod error: {response.status_code} - {response.text}"
                }
                
        except requests.Timeout:
            return {
                "status": "error",
                "message": "RunPod job timed out"
            }
        except Exception as e:
            logger.error(f"Error in sync RunPod job: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a RunPod job
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job status information
        """
        try:
            url = f"{self.config.base_url}/{self.config.endpoint_id}/status/{job_id}"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": JobStatus.FAILED.value,
                    "message": f"Failed to get status: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {
                "status": JobStatus.FAILED.value,
                "message": str(e)
            }
    
    def wait_for_job(self, job_id: str, callback=None) -> Dict[str, Any]:
        """
        Wait for a job to complete
        
        Args:
            job_id: Job ID to wait for
            callback: Optional callback function for status updates
            
        Returns:
            Final job result
        """
        start_time = time.time()
        
        while time.time() - start_time < self.config.timeout:
            status = self.get_job_status(job_id)
            
            # Call callback if provided
            if callback:
                callback(status)
            
            job_status = status.get("status")
            
            if job_status == JobStatus.COMPLETED.value:
                return {
                    "status": "success",
                    "output": status.get("output", {}),
                    "execution_time": status.get("executionTime", 0)
                }
            elif job_status in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                return {
                    "status": "error",
                    "message": status.get("error", "Job failed")
                }
            
            time.sleep(self.config.poll_interval)
        
        # Timeout reached
        return {
            "status": "error",
            "message": "Job timed out"
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        try:
            url = f"{self.config.base_url}/{self.config.endpoint_id}/cancel/{job_id}"
            
            response = requests.post(
                url,
                headers=self.headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error cancelling job: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check RunPod endpoint health
        
        Returns:
            Health status information
        """
        try:
            url = f"{self.config.base_url}/{self.config.endpoint_id}/health"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "workers": data.get("workers", {}),
                    "queue": data.get("queue", {})
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Health check failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class RunPodProcessor:
    """High-level processor for video tasks using RunPod"""
    
    def __init__(self, client: Optional[RunPodClient] = None):
        """Initialize processor"""
        self.client = client or RunPodClient()
    
    def process_video_pipeline(
        self,
        request_id: str,
        script: str,
        video_urls: List[str],
        target_duration: int,
        voiceover_url: Optional[str] = None,
        callback=None
    ) -> Dict[str, Any]:
        """
        Process complete video pipeline through RunPod
        
        Args:
            request_id: Unique request ID
            script: Script text
            video_urls: List of video URLs
            target_duration: Target duration in seconds
            voiceover_url: Optional voiceover audio URL
            callback: Progress callback function
            
        Returns:
            Processing result
        """
        job_input = {
            "task_type": "full_pipeline",
            "request_id": request_id,
            "inputs": {
                "script": script,
                "videos": video_urls,
                "duration": target_duration,
                "voiceover": voiceover_url
            }
        }
        
        # Use sync job for simpler handling
        result = self.client.submit_sync_job(job_input, timeout=600)  # 10 minute timeout
        
        if callback:
            callback(result)
        
        return result
    
    def merge_videos(self, request_id: str, video_urls: List[str]) -> Dict[str, Any]:
        """Merge multiple videos"""
        job_input = {
            "task_type": "merge_videos",
            "request_id": request_id,
            "inputs": {
                "videos": video_urls
            }
        }
        
        return self.client.submit_sync_job(job_input, timeout=300)
    
    def compress_video(self, request_id: str, video_url: str) -> Dict[str, Any]:
        """Compress video for processing"""
        job_input = {
            "task_type": "compress_video",
            "request_id": request_id,
            "inputs": {
                "video": video_url
            }
        }
        
        return self.client.submit_sync_job(job_input, timeout=300)
    
    def extract_segments(
        self,
        request_id: str,
        video_url: str,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract video segments"""
        job_input = {
            "task_type": "extract_segments",
            "request_id": request_id,
            "inputs": {
                "video": video_url,
                "segments": segments
            }
        }
        
        return self.client.submit_sync_job(job_input, timeout=300)
    
    def add_voiceover(
        self,
        request_id: str,
        video_url: str,
        audio_url: str
    ) -> Dict[str, Any]:
        """Add voiceover to video"""
        job_input = {
            "task_type": "add_voiceover",
            "request_id": request_id,
            "inputs": {
                "video": video_url,
                "audio": audio_url
            }
        }
        
        return self.client.submit_sync_job(job_input, timeout=300)