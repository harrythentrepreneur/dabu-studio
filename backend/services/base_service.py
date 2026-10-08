"""
Base service class providing common functionality for all services.
"""

from abc import ABC
from pathlib import Path
from typing import Optional

from utils.logger import get_logger


class BaseService(ABC):
    """Base class for all services providing common functionality."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize base service.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.logger = get_logger(self.__class__.__name__)
        self.temp_dir = temp_dir or Path(__file__).parent.parent / 'temp'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_file_exists(self, file_path: Path, error_message: str = None) -> None:
        """
        Ensure a file exists, raising appropriate error if not.
        
        Args:
            file_path: Path to check
            error_message: Custom error message
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            message = error_message or f"File not found: {file_path}"
            self.logger.error(message)
            raise FileNotFoundError(message)
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """
        Get file size in megabytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in MB
        """
        self.ensure_file_exists(file_path)
        return file_path.stat().st_size / (1024 * 1024)