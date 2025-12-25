"""
Structured logging middleware for FastAPI.
"""

import time
import logging
from uuid import uuid4
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.analytics_service import get_analytics_service


logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging and metrics collection.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log structured data."""
        # Generate request ID for correlation
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Extract user context if available
        user_id = None
        family_unit_id = None
        role = None
        
        try:
            # Try to get user from request state (set by auth dependency)
            if hasattr(request.state, "user"):
                user = request.state.user
                user_id = str(user.user_id) if hasattr(user, "user_id") else str(user.sub) if hasattr(user, "sub") else None
                family_unit_id = str(user.family_unit_id) if hasattr(user, "family_unit_id") else None
                role = user.role if hasattr(user, "role") else None
        except Exception:
            pass
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_id": user_id,
                "family_unit_id": family_unit_id,
                "role": role,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "family_unit_id": family_unit_id
                }
            )
            
            # Record metrics
            try:
                analytics = get_analytics_service()
                await analytics.record_timer(
                    metric_name="api_request_duration_ms",
                    duration_ms=duration_ms,
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": str(response.status_code),
                        "family_unit_id": family_unit_id or "anonymous"
                    }
                )
                
                await analytics.increment_counter(
                    metric_name="api_request_count",
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": str(response.status_code),
                        "family_unit_id": family_unit_id or "anonymous"
                    }
                )
            except Exception as e:
                logger.error(f"Failed to record metrics: {e}", exc_info=True)
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "family_unit_id": family_unit_id
                },
                exc_info=True
            )
            
            # Record error metric
            try:
                analytics = get_analytics_service()
                await analytics.increment_counter(
                    metric_name="api_request_errors",
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "error_type": type(e).__name__,
                        "family_unit_id": family_unit_id or "anonymous"
                    }
                )
            except Exception:
                pass
            
            raise

