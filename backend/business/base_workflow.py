"""
Base workflow class providing common functionality for business workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pathlib import Path

from utils.logger import get_logger


class BaseWorkflow(ABC):
    """Base class for business workflows."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize base workflow.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.logger = get_logger(self.__class__.__name__)
        self.temp_dir = temp_dir or Path(__file__).parent.parent / 'temp'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Workflow state
        self._status_emitter = None
        self._current_step = 0
        self._total_steps = 1
        
    def set_status_emitter(self, emitter: Any) -> None:
        """Set status emitter for real-time updates."""
        self._status_emitter = emitter
    
    def emit_status(self, step_name: str, progress: int, message: str = "", error: str = "") -> None:
        """Emit status update if emitter is available."""
        if self._status_emitter:
            self._status_emitter.emit_status(
                step=self._current_step,
                step_name=step_name,
                progress=progress,
                message=message,
                error=error
            )
    
    def emit_completion(self, success: bool, result_data: Dict = None, error_message: str = "") -> None:
        """Emit workflow completion status."""
        if self._status_emitter:
            self._status_emitter.emit_complete(
                success=success,
                result_data=result_data,
                error_message=error_message
            )
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the workflow. Must be implemented by subclasses."""
        pass