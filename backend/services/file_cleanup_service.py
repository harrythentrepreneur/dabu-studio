"""
File cleanup service for managing temporary files and disk space.
"""

import time
from pathlib import Path
from typing import List

from .base_service import BaseService
from config.constants import (
    TEMP_FILE_PATTERNS,
    TEMP_FILE_MAX_AGE_HOURS,
    CLEANUP_SIZE_THRESHOLD_MB
)


class FileCleanupService(BaseService):
    """Service for cleaning up temporary files and managing disk space."""
    
    def cleanup_temp_files(self, files_to_clean: List[Path]) -> None:
        """
        Clean up specified temporary files.
        
        Args:
            files_to_clean: List of file paths to delete
        """
        for file_path in files_to_clean:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.logger.debug(f"Deleted temporary file: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to delete {file_path}: {e}")
    
    def cleanup_old_temp_files(self, max_age_hours: int = TEMP_FILE_MAX_AGE_HOURS) -> dict:
        """
        Clean up old temporary files to prevent disk space issues.
        
        Args:
            max_age_hours: Delete files older than this many hours
            
        Returns:
            Dictionary with cleanup statistics
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        cleaned_size = 0
        failed_count = 0
        
        for pattern in TEMP_FILE_PATTERNS:
            for file_path in self.temp_dir.glob(pattern):
                try:
                    # Check file age
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += file_size
                        self.logger.debug(f"Cleaned old temp file: {file_path.name}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean {file_path}: {e}")
                    failed_count += 1
        
        cleaned_mb = cleaned_size / (1024 * 1024)
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned {cleaned_count} old temp files ({cleaned_mb:.1f}MB freed)")
        
        return {
            'cleaned_count': cleaned_count,
            'cleaned_size_mb': cleaned_mb,
            'failed_count': failed_count,
            'max_age_hours': max_age_hours
        }
    
    def get_temp_dir_size(self) -> dict:
        """
        Get current temporary directory size and file count.
        
        Returns:
            Dictionary with size statistics
        """
        total_size = 0
        file_count = 0
        
        try:
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        except Exception as e:
            self.logger.warning(f"Failed to calculate temp dir size: {e}")
        
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            'total_size_mb': total_size_mb,
            'file_count': file_count,
            'directory': str(self.temp_dir)
        }
    
    def cleanup_if_needed(self, force: bool = False) -> dict:
        """
        Clean up temporary files if directory size exceeds threshold.
        
        Args:
            force: Force cleanup regardless of size
            
        Returns:
            Dictionary with cleanup results
        """
        size_info = self.get_temp_dir_size()
        cleanup_needed = force or size_info['total_size_mb'] > CLEANUP_SIZE_THRESHOLD_MB
        
        if not cleanup_needed:
            self.logger.debug(f"Cleanup not needed: {size_info['total_size_mb']:.1f}MB < {CLEANUP_SIZE_THRESHOLD_MB}MB")
            return {
                'cleanup_performed': False,
                'reason': 'size_below_threshold',
                'current_size_mb': size_info['total_size_mb'],
                'threshold_mb': CLEANUP_SIZE_THRESHOLD_MB
            }
        
        self.logger.info(f"Cleaning temp directory: {size_info['total_size_mb']:.1f}MB")
        cleanup_results = self.cleanup_old_temp_files()
        
        # Get new size after cleanup
        new_size_info = self.get_temp_dir_size()
        
        return {
            'cleanup_performed': True,
            'reason': 'forced' if force else 'size_exceeded_threshold',
            'old_size_mb': size_info['total_size_mb'],
            'new_size_mb': new_size_info['total_size_mb'],
            'freed_mb': cleanup_results['cleaned_size_mb'],
            'cleaned_files': cleanup_results['cleaned_count'],
            'failed_files': cleanup_results['failed_count']
        }
    
    def cleanup_specific_patterns(self, patterns: List[str]) -> dict:
        """
        Clean up files matching specific patterns.
        
        Args:
            patterns: List of glob patterns to match
            
        Returns:
            Dictionary with cleanup statistics
        """
        cleaned_count = 0
        cleaned_size = 0
        
        for pattern in patterns:
            for file_path in self.temp_dir.glob(pattern):
                try:
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += file_size
                        self.logger.debug(f"Cleaned file: {file_path.name}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean {file_path}: {e}")
        
        cleaned_mb = cleaned_size / (1024 * 1024)
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned {cleaned_count} files matching patterns ({cleaned_mb:.1f}MB freed)")
        
        return {
            'cleaned_count': cleaned_count,
            'cleaned_size_mb': cleaned_mb,
            'patterns': patterns
        }