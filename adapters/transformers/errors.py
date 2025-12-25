"""
Error transformation utilities.
"""

from typing import Any, Dict, Optional
from httpx import HTTPStatusError, RequestError


class ErrorTransformer:
    """Transform backend errors to frontend format."""
    
    # Error code mapping
    ERROR_CODES = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    
    def __init__(self, config=None):
        """Initialize error transformer."""
        from adapters.config import get_adapter_config
        self.config = config or get_adapter_config()
    
    def transform_error(
        self,
        error: Exception,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transform error to frontend format.
        
        Args:
            error: Exception to transform
            request_path: Request path (for context)
            request_method: Request method (for context)
        
        Returns:
            Error response dict
        """
        if isinstance(error, HTTPStatusError):
            return self._transform_http_error(
                error, request_path, request_method
            )
        
        if isinstance(error, RequestError):
            return self._transform_request_error(
                error, request_path, request_method
            )
        
        # Generic error
        return self._transform_generic_error(
            error, request_path, request_method
        )
    
    def _transform_http_error(
        self,
        error: HTTPStatusError,
        request_path: Optional[str],
        request_method: Optional[str],
    ) -> Dict[str, Any]:
        """Transform HTTP status error."""
        status_code = error.response.status_code
        error_code = self.ERROR_CODES.get(status_code, "HTTP_ERROR")
        
        # Try to extract error details from response
        error_detail = None
        error_message = None
        
        try:
            response_data = error.response.json()
            
            # FastAPI error format
            if "detail" in response_data:
                error_detail = response_data["detail"]
            
            # Check for validation errors
            if isinstance(error_detail, list):
                # Pydantic validation errors
                error_message = "Validation failed"
                error_detail = {
                    "validation_errors": error_detail,
                }
            elif isinstance(error_detail, dict):
                error_message = error_detail.get("message") or error_detail.get("detail")
            elif isinstance(error_detail, str):
                error_message = error_detail
                error_detail = {"message": error_detail}
            
        except Exception:
            # Could not parse JSON
            error_message = error.response.text or self._get_default_message(status_code)
            error_detail = {"message": error_message}
        
        if not error_message:
            error_message = self._get_default_message(status_code)
        
        if not error_detail:
            error_detail = {"message": error_message}
        
        # Don't expose internal errors
        if not self.config.expose_internal_errors and status_code >= 500:
            error_message = self.config.default_error_message
            error_detail = {"message": error_message}
        
        return {
            "error": {
                "code": error_code,
                "message": error_message,
                "status_code": status_code,
                "details": error_detail,
            }
        }
    
    def _transform_request_error(
        self,
        error: RequestError,
        request_path: Optional[str],
        request_method: Optional[str],
    ) -> Dict[str, Any]:
        """Transform request error (network/connection)."""
        error_message = "Network error: Unable to connect to server"
        
        # Provide more specific messages for common errors
        error_str = str(error).lower()
        if "timeout" in error_str:
            error_message = "Request timeout: Server did not respond in time"
        elif "connection" in error_str:
            error_message = "Connection error: Unable to reach server"
        
        return {
            "error": {
                "code": "NETWORK_ERROR",
                "message": error_message,
                "details": {
                    "message": str(error) if self.config.expose_internal_errors else error_message,
                },
            }
        }
    
    def _transform_generic_error(
        self,
        error: Exception,
        request_path: Optional[str],
        request_method: Optional[str],
    ) -> Dict[str, Any]:
        """Transform generic exception."""
        error_message = self.config.default_error_message
        
        if self.config.expose_internal_errors:
            error_message = str(error)
        
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": error_message,
                "details": {
                    "message": str(error) if self.config.expose_internal_errors else error_message,
                },
            }
        }
    
    def _get_default_message(self, status_code: int) -> str:
        """Get default error message for status code."""
        messages = {
            400: "Invalid request",
            401: "Authentication required",
            403: "Access denied",
            404: "Resource not found",
            409: "Conflict: Resource already exists",
            422: "Validation error",
            500: "Internal server error",
            502: "Bad gateway",
            503: "Service unavailable",
        }
        return messages.get(status_code, "An error occurred")

