"""
Structured logging for adapter operations.
"""

import logging
import time
from typing import Optional, Dict, Any
from uuid import uuid4


class AdapterLogger:
    """Structured logger for adapter operations."""
    
    def __init__(self, name: str = "adapters"):
        """Initialize adapter logger."""
        self.logger = logging.getLogger(name)
    
    def log_request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log incoming request.
        
        Args:
            method: HTTP method
            path: Request path
            user_id: User ID (if available)
            request_id: Request ID
            **kwargs: Additional context
        """
        request_id = request_id or str(uuid4())
        
        self.logger.info(
            "Adapter request",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "user_id": user_id,
                **kwargs,
            }
        )
        
        return request_id
    
    def log_response(
        self,
        request_id: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """
        Log response.
        
        Args:
            request_id: Request ID
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context
        """
        self.logger.info(
            "Adapter response",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "duration_ms": duration_ms,
                **kwargs,
            }
        )
    
    def log_error(
        self,
        request_id: str,
        error: Exception,
        **kwargs
    ):
        """
        Log error.
        
        Args:
            request_id: Request ID
            error: Exception
            **kwargs: Additional context
        """
        self.logger.error(
            "Adapter error",
            extra={
                "request_id": request_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **kwargs,
            },
            exc_info=True,
        )
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        family_unit_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log business event.
        
        Args:
            event_type: Event type
            user_id: User ID
            family_unit_id: Family unit ID
            metadata: Event metadata
        """
        self.logger.info(
            "Adapter event",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "family_unit_id": family_unit_id,
                "metadata": metadata or {},
            }
        )


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self):
        """Initialize timer."""
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and calculate duration."""
        if self.start_time:
            self.duration_ms = (time.time() - self.start_time) * 1000
    
    @property
    def duration(self) -> float:
        """Get duration in milliseconds."""
        return self.duration_ms or 0.0

