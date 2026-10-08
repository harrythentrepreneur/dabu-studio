"""
Disk cleanup utilities to prevent disk space issues.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
from utils.logger import get_logger


class DiskCleanupService:
    """Service for managing disk space and cleaning up old files."""
    
    def __init__(self, temp_dir: Path, output_dir: Path, min_free_gb: float = 5.0):
        """
        Initialize disk cleanup service.
        
        Args:
            temp_dir: Temporary files directory
            output_dir: Output files directory
            min_free_gb: Minimum free space in GB to maintain
        """
        self.temp_dir = temp_dir
        self.output_dir = output_dir
        self.min_free_gb = min_free_gb
        self.logger = get_logger(__name__)
    
    def check_disk_space(self) -> Tuple[float, float]:
        """
        Check available disk space.
        
        Returns:
            Tuple of (free_gb, total_gb)
        """
        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024 ** 3)
        total_gb = stat.total / (1024 ** 3)
        return free_gb, total_gb
    
    def cleanup_old_temp_files(self, hours: int = 2) -> int:
        """
        Clean up temporary files older than specified hours.
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Number of files deleted
        """
        if not self.temp_dir.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        deleted_count = 0
        freed_space = 0
        
        for file_path in self.temp_dir.glob("*"):
            try:
                # Check file age
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    if file_path.is_file():
                        file_path.unlink()
                    else:
                        shutil.rmtree(file_path)
                    deleted_count += 1
                    freed_space += file_size
                    self.logger.debug(f"Deleted old temp file: {file_path.name}")
            except Exception as e:
                self.logger.warning(f"Failed to delete {file_path}: {e}")
        
        if deleted_count > 0:
            freed_mb = freed_space / (1024 * 1024)
            self.logger.info(f"Cleaned up {deleted_count} old temp files, freed {freed_mb:.1f}MB")
        
        return deleted_count
    
    def cleanup_if_needed(self) -> bool:
        """
        Check disk space and cleanup if needed.
        
        Returns:
            True if cleanup was performed, False otherwise
        """
        free_gb, total_gb = self.check_disk_space()
        
        self.logger.info(f"Disk space: {free_gb:.1f}GB free of {total_gb:.1f}GB total")
        
        if free_gb < self.min_free_gb:
            self.logger.warning(f"Low disk space detected: {free_gb:.1f}GB < {self.min_free_gb}GB minimum")
            
            # First try cleaning old temp files
            deleted = self.cleanup_old_temp_files(hours=1)
            
            # Check again
            free_gb, _ = self.check_disk_space()
            
            if free_gb < self.min_free_gb:
                # More aggressive cleanup - delete all temp files
                self.logger.warning("Still low on space, performing aggressive cleanup")
                deleted += self.cleanup_all_temp_files()
            
            return deleted > 0
        
        return False
    
    def cleanup_all_temp_files(self) -> int:
        """
        Clean up all temporary files (emergency cleanup).
        
        Returns:
            Number of files deleted
        """
        if not self.temp_dir.exists():
            return 0
        
        deleted_count = 0
        
        for file_path in self.temp_dir.glob("merged_*"):
            try:
                file_path.unlink()
                deleted_count += 1
                self.logger.debug(f"Deleted temp file: {file_path.name}")
            except Exception as e:
                self.logger.warning(f"Failed to delete {file_path}: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"Emergency cleanup: deleted {deleted_count} temp files")
        
        return deleted_count
    
    def get_temp_dir_size(self) -> float:
        """
        Get total size of temp directory in MB.
        
        Returns:
            Size in MB
        """
        if not self.temp_dir.exists():
            return 0.0
        
        total_size = 0
        for file_path in self.temp_dir.glob("**/*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)