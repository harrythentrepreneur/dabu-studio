"""
File system utilities for TikTok Video Ad Automation.

This module provides common file system operations including:
- File validation and existence checks
- Temporary file management
- Directory operations
- File cleanup utilities
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional, Set
from .logger import get_logger
from .exceptions import VideoNotFoundError


logger = get_logger(__name__)


def ensure_file_exists(file_path: Path, error_message: Optional[str] = None) -> None:
    """
    Ensure a file exists, raising an error if it doesn't.
    
    Args:
        file_path: Path to check
        error_message: Custom error message
        
    Raises:
        VideoNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        message = error_message or f"File not found: {file_path}"
        raise VideoNotFoundError(message)


def ensure_directory_exists(dir_path: Path, create: bool = True) -> None:
    """
    Ensure a directory exists, optionally creating it.
    
    Args:
        dir_path: Path to directory
        create: Whether to create the directory if it doesn't exist
        
    Raises:
        FileNotFoundError: If directory doesn't exist and create=False
    """
    if not dir_path.exists():
        if create:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")
        else:
            raise FileNotFoundError(f"Directory not found: {dir_path}")


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in MB.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
        
    Raises:
        VideoNotFoundError: If file doesn't exist
    """
    ensure_file_exists(file_path)
    return file_path.stat().st_size / (1024 * 1024)


def cleanup_files(file_paths: List[Path], ignore_errors: bool = True) -> int:
    """
    Clean up multiple files.
    
    Args:
        file_paths: List of file paths to clean up
        ignore_errors: Whether to ignore cleanup errors
        
    Returns:
        Number of files successfully cleaned up
    """
    cleaned_count = 0
    
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
                cleaned_count += 1
                logger.debug(f"Cleaned up: {file_path.name}")
        except Exception as e:
            if ignore_errors:
                logger.warning(f"Failed to clean up {file_path.name}: {e}")
            else:
                raise
    
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} files")
    
    return cleaned_count


def cleanup_old_files(
    directory: Path, 
    patterns: List[str], 
    max_age_hours: int = 2,
    ignore_errors: bool = True
) -> int:
    """
    Clean up old files matching patterns in a directory.
    
    Args:
        directory: Directory to clean
        patterns: List of glob patterns to match
        max_age_hours: Maximum age of files to keep (in hours)
        ignore_errors: Whether to ignore cleanup errors
        
    Returns:
        Number of files cleaned up
    """
    if not directory.exists():
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    for pattern in patterns:
        for file_path in directory.glob(pattern):
            try:
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Cleaned up old file: {file_path.name}")
            except Exception as e:
                if ignore_errors:
                    logger.warning(f"Failed to clean old file {file_path.name}: {e}")
                else:
                    raise
    
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} old files from {directory}")
    
    return cleaned_count


def cleanup_directory(directory: Path, ignore_errors: bool = True) -> bool:
    """
    Remove entire directory and its contents.
    
    Args:
        directory: Directory to remove
        ignore_errors: Whether to ignore removal errors
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if directory.exists():
            shutil.rmtree(directory)
            logger.info(f"Removed directory: {directory}")
            return True
        return True
    except Exception as e:
        if ignore_errors:
            logger.warning(f"Failed to remove directory {directory}: {e}")
            return False
        else:
            raise


def copy_file(source: Path, destination: Path, overwrite: bool = True) -> Path:
    """
    Copy a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Whether to overwrite existing destination
        
    Returns:
        Path to destination file
        
    Raises:
        VideoNotFoundError: If source file doesn't exist
        FileExistsError: If destination exists and overwrite=False
    """
    ensure_file_exists(source)
    
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Destination file already exists: {destination}")
    
    # Ensure destination directory exists
    ensure_directory_exists(destination.parent)
    
    shutil.copy2(source, destination)
    logger.debug(f"Copied {source.name} to {destination}")
    
    return destination


def move_file(source: Path, destination: Path, overwrite: bool = True) -> Path:
    """
    Move a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Whether to overwrite existing destination
        
    Returns:
        Path to destination file
        
    Raises:
        VideoNotFoundError: If source file doesn't exist
        FileExistsError: If destination exists and overwrite=False
    """
    ensure_file_exists(source)
    
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Destination file already exists: {destination}")
    
    # Ensure destination directory exists
    ensure_directory_exists(destination.parent)
    
    shutil.move(str(source), str(destination))
    logger.debug(f"Moved {source.name} to {destination}")
    
    return destination


def find_files_by_extension(
    directory: Path, 
    extensions: Set[str], 
    recursive: bool = False
) -> List[Path]:
    """
    Find all files with specified extensions in a directory.
    
    Args:
        directory: Directory to search
        extensions: Set of file extensions (with or without dots)
        recursive: Whether to search recursively
        
    Returns:
        List of matching file paths
    """
    if not directory.exists():
        return []
    
    # Normalize extensions (ensure they start with a dot)
    normalized_extensions = set()
    for ext in extensions:
        if not ext.startswith('.'):
            ext = f'.{ext}'
        normalized_extensions.add(ext.lower())
    
    files = []
    pattern = '**/*' if recursive else '*'
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in normalized_extensions:
            files.append(file_path)
    
    return sorted(files)


def get_available_filename(base_path: Path) -> Path:
    """
    Get an available filename by adding a counter if the base path exists.
    
    Args:
        base_path: Desired file path
        
    Returns:
        Available file path (may be the same as base_path)
    """
    if not base_path.exists():
        return base_path
    
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def create_temp_file(
    temp_dir: Path, 
    prefix: str = "temp_", 
    suffix: str = ".tmp"
) -> Path:
    """
    Create a temporary file path in the specified directory.
    
    Args:
        temp_dir: Temporary directory
        prefix: Filename prefix
        suffix: Filename suffix/extension
        
    Returns:
        Path to temporary file
    """
    ensure_directory_exists(temp_dir)
    
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    temp_filename = f"{prefix}{unique_id}{suffix}"
    
    return temp_dir / temp_filename