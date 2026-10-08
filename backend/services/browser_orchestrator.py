"""
Browser Orchestrator - Manages concurrent browser automation for CapCut Web
Optimized for RunPod serverless deployment with resource management
"""

import asyncio
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from utils.logger import get_logger

logger = get_logger(__name__)


class ProcessingStatus(Enum):
    """Status of video processing"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingRequest:
    """Data class for processing requests"""
    request_id: str
    video_path: str
    caption_style: str
    status: ProcessingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class QueueManager:
    """Manages the processing queue with priority and retry logic"""
    
    def __init__(self, max_queue_size: int = 100):
        """
        Initialize queue manager
        
        Args:
            max_queue_size: Maximum number of requests in queue
        """
        self.max_queue_size = max_queue_size
        self.queue: deque[ProcessingRequest] = deque()
        self.processing: Dict[str, ProcessingRequest] = {}
        self.completed: Dict[str, ProcessingRequest] = {}
        self.lock = threading.Lock()
        
    def add_request(self, request: ProcessingRequest) -> bool:
        """
        Add a request to the queue
        
        Args:
            request: Processing request to add
            
        Returns:
            True if added, False if queue is full
        """
        with self.lock:
            if len(self.queue) >= self.max_queue_size:
                return False
                
            self.queue.append(request)
            logger.info(f"Added request {request.request_id} to queue. Queue size: {len(self.queue)}")
            return True
            
    def get_next_request(self) -> Optional[ProcessingRequest]:
        """
        Get the next request from the queue
        
        Returns:
            Next request or None if queue is empty
        """
        with self.lock:
            if not self.queue:
                return None
                
            request = self.queue.popleft()
            request.status = ProcessingStatus.PROCESSING
            request.started_at = datetime.now()
            self.processing[request.request_id] = request
            
            logger.info(f"Processing request {request.request_id}. Queue size: {len(self.queue)}")
            return request
            
    def mark_completed(self, request_id: str, result: Dict[str, Any]):
        """Mark a request as completed"""
        with self.lock:
            if request_id in self.processing:
                request = self.processing.pop(request_id)
                request.status = ProcessingStatus.COMPLETED
                request.completed_at = datetime.now()
                request.result = result
                self.completed[request_id] = request
                logger.info(f"Request {request_id} completed successfully")
                
    def mark_failed(self, request_id: str, error: str):
        """Mark a request as failed and potentially retry"""
        with self.lock:
            if request_id in self.processing:
                request = self.processing.pop(request_id)
                request.error = error
                request.retry_count += 1
                
                if request.retry_count < request.max_retries:
                    # Re-queue for retry
                    request.status = ProcessingStatus.QUEUED
                    self.queue.append(request)
                    logger.info(f"Request {request_id} failed, retrying ({request.retry_count}/{request.max_retries})")
                else:
                    # Max retries reached
                    request.status = ProcessingStatus.FAILED
                    request.completed_at = datetime.now()
                    self.completed[request_id] = request
                    logger.error(f"Request {request_id} failed after {request.retry_count} retries: {error}")
                    
    def get_status(self, request_id: str) -> Optional[ProcessingRequest]:
        """Get the status of a request"""
        with self.lock:
            # Check in all locations
            for request in self.queue:
                if request.request_id == request_id:
                    return request
                    
            if request_id in self.processing:
                return self.processing[request_id]
                
            if request_id in self.completed:
                return self.completed[request_id]
                
            return None
            
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            return {
                "queued": len(self.queue),
                "processing": len(self.processing),
                "completed": len(self.completed),
                "total": len(self.queue) + len(self.processing) + len(self.completed)
            }
            
    def cleanup_old_completed(self, max_age_hours: int = 24):
        """Clean up old completed requests"""
        with self.lock:
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            to_remove = []
            
            for request_id, request in self.completed.items():
                if request.completed_at and request.completed_at < cutoff:
                    to_remove.append(request_id)
                    
            for request_id in to_remove:
                del self.completed[request_id]
                
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old completed requests")


class BrowserOrchestrator:
    """
    Orchestrates multiple browser instances for concurrent CapCut Web processing.
    Designed for RunPod serverless with resource optimization.
    """
    
    def __init__(
        self,
        max_workers: int = 5,
        max_queue_size: int = 100,
        enable_monitoring: bool = True
    ):
        """
        Initialize browser orchestrator
        
        Args:
            max_workers: Maximum concurrent browser workers
            max_queue_size: Maximum queue size
            enable_monitoring: Enable resource monitoring
        """
        self.max_workers = max_workers
        self.queue_manager = QueueManager(max_queue_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.workers: List[Future] = []
        self.running = False
        self.enable_monitoring = enable_monitoring
        
        # Import CapCut service lazily to avoid circular imports.
        # Fallback to available implementations if legacy module is missing.
        try:
            from services.capcut_web_service import CapCutWebService  # type: ignore
            self.service_class = CapCutWebService
        except Exception:
            try:
                from services.intelligent_capcut_service import (
                    IntelligentCapCutService as CapCutWebService,  # type: ignore
                )
                self.service_class = CapCutWebService
                logger.info("Using IntelligentCapCutService as CapCutWebService")
            except Exception:
                from services.mcp_capcut_service_enhanced import (
                    MCPCapCutServiceEnhanced as CapCutWebService,  # type: ignore
                )
                self.service_class = CapCutWebService
                logger.info("Using MCPCapCutServiceEnhanced as CapCutWebService")
        
        # Resource monitoring
        self.resource_stats = {
            "total_processed": 0,
            "total_failed": 0,
            "average_processing_time": 0,
            "current_memory_mb": 0,
            "current_cpu_percent": 0
        }
        
        # RunPod specific configuration
        self.is_runpod = bool(os.environ.get('RUNPOD_POD_ID'))
        if self.is_runpod:
            logger.info(f"Running on RunPod pod: {os.environ.get('RUNPOD_POD_ID')}")
            
    def start(self):
        """Start the orchestrator and worker threads"""
        if self.running:
            logger.warning("Orchestrator already running")
            return
            
        self.running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = self.executor.submit(self._worker_loop, i)
            self.workers.append(worker)
            
        # Start monitoring thread if enabled
        if self.enable_monitoring:
            self.executor.submit(self._monitoring_loop)
            
        # Start cleanup thread
        self.executor.submit(self._cleanup_loop)
        
        logger.info(f"Browser orchestrator started with {self.max_workers} workers")
        
    def stop(self):
        """Stop the orchestrator and all workers"""
        logger.info("Stopping browser orchestrator...")
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            try:
                worker.result(timeout=10)
            except Exception as e:
                logger.error(f"Error stopping worker: {e}")
                
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Browser orchestrator stopped")
        
    def submit_request(
        self,
        video_path: str,
        caption_style: str = "TikTok Bold",
        request_id: Optional[str] = None
    ) -> str:
        """
        Submit a video processing request
        
        Args:
            video_path: Path to video file
            caption_style: Caption style to apply
            request_id: Optional request ID
            
        Returns:
            Request ID for tracking
        """
        request_id = request_id or f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        request = ProcessingRequest(
            request_id=request_id,
            video_path=video_path,
            caption_style=caption_style,
            status=ProcessingStatus.QUEUED,
            created_at=datetime.now()
        )
        
        if not self.queue_manager.add_request(request):
            raise Exception("Queue is full. Please try again later.")
            
        return request_id
        
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a request
        
        Args:
            request_id: Request ID to check
            
        Returns:
            Status dictionary or None if not found
        """
        request = self.queue_manager.get_status(request_id)
        
        if not request:
            return None
            
        return {
            "request_id": request.request_id,
            "status": request.status.value,
            "created_at": request.created_at.isoformat(),
            "started_at": request.started_at.isoformat() if request.started_at else None,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "result": request.result,
            "error": request.error,
            "retry_count": request.retry_count
        }
        
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        queue_stats = self.queue_manager.get_queue_stats()
        
        return {
            "queue": queue_stats,
            "workers": {
                "max": self.max_workers,
                "active": sum(1 for w in self.workers if not w.done())
            },
            "resources": self.resource_stats,
            "is_runpod": self.is_runpod
        }
        
    async def _process_request_async(self, request: ProcessingRequest) -> Dict[str, Any]:
        """Process a request asynchronously"""
        service = self.service_class()
        
        try:
            result = await service.process_video_with_captions(
                video_path=request.video_path,
                caption_style=request.caption_style,
                request_id=request.request_id
            )
            
            # Update statistics
            if result.get("success"):
                self.resource_stats["total_processed"] += 1
                
                # Update average processing time
                if result.get("processing_time"):
                    current_avg = self.resource_stats["average_processing_time"]
                    total = self.resource_stats["total_processed"]
                    new_avg = ((current_avg * (total - 1)) + result["processing_time"]) / total
                    self.resource_stats["average_processing_time"] = new_avg
            else:
                self.resource_stats["total_failed"] += 1
                
            return result
            
        finally:
            await service.shutdown()
            
    def _worker_loop(self, worker_id: int):
        """Worker loop that processes requests from the queue"""
        logger.info(f"Worker {worker_id} started")
        
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                # Get next request from queue
                request = self.queue_manager.get_next_request()
                
                if not request:
                    # No requests, wait a bit
                    time.sleep(1)
                    continue
                    
                logger.info(f"Worker {worker_id} processing request {request.request_id}")
                
                # Process the request
                result = loop.run_until_complete(
                    self._process_request_async(request)
                )
                
                # Update request status
                if result.get("success"):
                    self.queue_manager.mark_completed(request.request_id, result)
                else:
                    self.queue_manager.mark_failed(
                        request.request_id,
                        result.get("error", "Unknown error")
                    )
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                if request:
                    self.queue_manager.mark_failed(request.request_id, str(e))
                    
        loop.close()
        logger.info(f"Worker {worker_id} stopped")
        
    def _monitoring_loop(self):
        """Monitor resource usage"""
        while self.running:
            try:
                # Get memory usage
                import psutil
                process = psutil.Process()
                self.resource_stats["current_memory_mb"] = process.memory_info().rss / 1024 / 1024
                self.resource_stats["current_cpu_percent"] = process.cpu_percent()
                
                # Log stats periodically
                if time.time() % 60 < 1:  # Every minute
                    logger.info(f"Resource stats: {self.resource_stats}")
                    
            except ImportError:
                # psutil not available
                pass
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
            time.sleep(5)
            
    def _cleanup_loop(self):
        """Cleanup old completed requests periodically"""
        while self.running:
            try:
                # Cleanup every hour
                self.queue_manager.cleanup_old_completed(max_age_hours=24)
                time.sleep(3600)  # Sleep for 1 hour
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                time.sleep(60)  # Sleep for 1 minute on error


# Global orchestrator instance (singleton pattern)
_orchestrator_instance: Optional[BrowserOrchestrator] = None


def get_orchestrator(
    max_workers: int = None,
    max_queue_size: int = None
) -> BrowserOrchestrator:
    """
    Get or create the global orchestrator instance
    
    Args:
        max_workers: Maximum concurrent workers (only used on first call)
        max_queue_size: Maximum queue size (only used on first call)
        
    Returns:
        Browser orchestrator instance
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        # Determine defaults based on environment
        if os.environ.get('RUNPOD_POD_ID'):
            # RunPod environment - optimize for serverless
            default_workers = int(os.environ.get('MAX_WORKERS', '10'))
            default_queue = int(os.environ.get('MAX_QUEUE_SIZE', '1000'))
        else:
            # Local/development environment
            default_workers = 3
            default_queue = 50
            
        _orchestrator_instance = BrowserOrchestrator(
            max_workers=max_workers or default_workers,
            max_queue_size=max_queue_size or default_queue
        )
        _orchestrator_instance.start()
        
    return _orchestrator_instance