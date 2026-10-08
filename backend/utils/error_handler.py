"""
Centralized error handling utilities for consistent error management.
"""

import traceback
from typing import Dict, Any, Type, Optional, Tuple, Union
from flask import jsonify, Response

from .logger import get_logger
from .exceptions import (
    VideoProcessingError,
    GeminiAPIError,
    ScriptValidationError,
    InsufficientVideoDataError,
    VideoNotFoundError,
    VideoFormatError,
    VideoSizeError,
    FFmpegError,
    DurationMismatchError
)
from config.constants import ERROR_MESSAGES


class ErrorHandler:
    """Centralized error handler with consistent formatting and logging."""
    
    # Map exception types to HTTP status codes
    ERROR_STATUS_CODES = {
        ValueError: 400,
        ScriptValidationError: 400,
        VideoSizeError: 400,
        VideoFormatError: 400,
        InsufficientVideoDataError: 400,
        DurationMismatchError: 400,
        VideoNotFoundError: 404,
        FileNotFoundError: 404,
        GeminiAPIError: 503,
        VideoProcessingError: 500,
        FFmpegError: 500,
        Exception: 500  # Default for unhandled errors
    }
    
    # Map exception types to user-friendly categories
    ERROR_CATEGORIES = {
        ValueError: 'validation_error',
        ScriptValidationError: 'script_validation',
        VideoSizeError: 'file_size_error',
        VideoFormatError: 'format_error',
        InsufficientVideoDataError: 'insufficient_content',
        DurationMismatchError: 'duration_error',
        VideoNotFoundError: 'file_not_found',
        FileNotFoundError: 'file_not_found',
        GeminiAPIError: 'ai_service_error',
        VideoProcessingError: 'processing_error',
        FFmpegError: 'encoding_error',
        Exception: 'internal_error'
    }
    
    def __init__(self, logger_name: str = __name__, debug: bool = False):
        """
        Initialize error handler.
        
        Args:
            logger_name: Name for logger
            debug: Whether to include debug information in responses
        """
        self.logger = get_logger(logger_name)
        self.debug = debug
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Handle an error with consistent formatting and logging.
        
        Args:
            error: Exception to handle
            context: Additional context about where error occurred
            extra_data: Extra data to include in response
            
        Returns:
            Tuple of (error_response_dict, http_status_code)
        """
        error_type = type(error)
        error_name = error_type.__name__
        
        # Log the error with full context
        log_message = f"{error_name}: {str(error)}"
        if context:
            log_message = f"[{context}] {log_message}"
        
        if error_type in [VideoProcessingError, FFmpegError, GeminiAPIError]:
            # These are serious errors that need full stack traces
            self.logger.error(log_message, exc_info=True)
        elif error_type in [ValueError, ScriptValidationError, VideoSizeError]:
            # These are user input errors, less severe
            self.logger.warning(log_message)
        else:
            # Unknown errors get full logging
            self.logger.error(log_message, exc_info=True)
        
        # Build error response
        response_data = self._build_error_response(error, context, extra_data)
        status_code = self._get_status_code(error_type)
        
        return response_data, status_code
    
    def handle_flask_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Handle an error and return a Flask JSON response.
        
        Args:
            error: Exception to handle
            context: Additional context
            extra_data: Extra data to include
            
        Returns:
            Flask JSON response
        """
        response_data, status_code = self.handle_error(error, context, extra_data)
        return jsonify(response_data), status_code
    
    def _build_error_response(
        self,
        error: Exception,
        context: Optional[str],
        extra_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build standardized error response."""
        error_type = type(error)
        error_name = error_type.__name__
        
        # Get user-friendly error category
        category = self.ERROR_CATEGORIES.get(error_type, 'internal_error')
        
        # Build base response
        response = {
            'error': category,
            'message': str(error),
            'type': error_name,
            'timestamp': self._get_timestamp()
        }
        
        # Add context if provided
        if context:
            response['context'] = context
        
        # Add debug information if in debug mode
        if self.debug:
            response['debug'] = {
                'traceback': traceback.format_exc(),
                'error_class': f"{error_type.__module__}.{error_name}"
            }
        
        # Add extra data if provided
        if extra_data:
            response.update(extra_data)
        
        # Add specific handling for certain error types
        if isinstance(error, InsufficientVideoDataError):
            if hasattr(error, 'required_duration') and hasattr(error, 'available_duration'):
                response['details'] = {
                    'required_duration': error.required_duration,
                    'available_duration': error.available_duration
                }
        
        elif isinstance(error, DurationMismatchError):
            if hasattr(error, 'target_duration') and hasattr(error, 'actual_duration'):
                response['details'] = {
                    'target_duration': error.target_duration,
                    'actual_duration': error.actual_duration,
                    'tolerance': getattr(error, 'tolerance', None)
                }
        
        elif isinstance(error, VideoSizeError):
            response['suggestion'] = 'Try compressing your video files or use fewer videos'
        
        elif isinstance(error, GeminiAPIError):
            response['suggestion'] = 'Try enabling mock mode for testing or check your API key'
        
        return response
    
    def _get_status_code(self, error_type: Type[Exception]) -> int:
        """Get HTTP status code for error type."""
        # Check specific type first, then fall back to base classes
        for exc_type, status_code in self.ERROR_STATUS_CODES.items():
            if issubclass(error_type, exc_type):
                return status_code
        
        # Default to 500 for unknown errors
        return 500
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def emit_error_to_status_emitter(
        self,
        error: Exception,
        emitter,
        context: Optional[str] = None
    ) -> None:
        """
        Emit error to status emitter for real-time updates.
        
        Args:
            error: Exception to emit
            emitter: Status event emitter
            context: Additional context
        """
        if not emitter:
            return
        
        error_name = type(error).__name__
        error_message = str(error)
        
        if context:
            error_message = f"[{context}] {error_message}"
        
        emitter.emit_complete(
            success=False,
            error_message=error_message
        )


# Global error handler instance
default_error_handler = ErrorHandler()


def handle_service_error(
    error: Exception,
    service_name: str,
    operation: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], int]:
    """
    Convenience function for handling service layer errors.
    
    Args:
        error: Exception to handle
        service_name: Name of service where error occurred
        operation: Operation being performed when error occurred
        extra_data: Extra data to include in response
        
    Returns:
        Tuple of (error_response_dict, http_status_code)
    """
    context = service_name
    if operation:
        context = f"{service_name}.{operation}"
    
    return default_error_handler.handle_error(error, context, extra_data)


def handle_workflow_error(
    error: Exception,
    workflow_name: str,
    step: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], int]:
    """
    Convenience function for handling workflow errors.
    
    Args:
        error: Exception to handle
        workflow_name: Name of workflow where error occurred
        step: Current workflow step
        extra_data: Extra data to include in response
        
    Returns:
        Tuple of (error_response_dict, http_status_code)
    """
    context = f"workflow:{workflow_name}"
    if step:
        context = f"{context}:{step}"
    
    return default_error_handler.handle_error(error, context, extra_data)


def wrap_service_method(service_name: str, method_name: str):
    """
    Decorator to wrap service methods with consistent error handling.
    
    Args:
        service_name: Name of the service
        method_name: Name of the method
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response, status_code = handle_service_error(
                    e, service_name, method_name
                )
                # Re-raise with additional context
                raise type(e)(f"[{service_name}.{method_name}] {str(e)}") from e
        return wrapper
    return decorator