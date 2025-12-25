"""
HTTP client for communicating with the backend API.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from uuid import uuid4

import httpx
from httpx import Response, RequestError, HTTPStatusError

from adapters.config import get_adapter_config

logger = logging.getLogger(__name__)


class AdapterClient:
    """HTTP client for backend API communication."""
    
    def __init__(self, config=None):
        """Initialize adapter client."""
        self.config = config or get_adapter_config()
        self.client = httpx.AsyncClient(
            base_url=self.config.backend_api_url,
            timeout=self.config.request_timeout_seconds,
            follow_redirects=True,
        )
    
    async def request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None,
    ) -> Response:
        """
        Make HTTP request to backend API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path (relative to base URL)
            token: Authentication token (Supabase JWT)
            json: Request body as JSON
            params: Query parameters
            headers: Additional headers
            request_id: Request ID for tracing
        
        Returns:
            HTTP response
        
        Raises:
            RequestError: For network/connection errors
            HTTPStatusError: For HTTP error responses
        """
        request_id = request_id or str(uuid4())
        
        # Prepare headers
        request_headers = {
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
        }
        
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        
        if headers:
            request_headers.update(headers)
        
        # Log request
        if self.config.log_requests:
            logger.info(
                "Adapter request",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "has_token": bool(token),
                }
            )
        
        start_time = time.time()
        
        try:
            # Make request with retry logic
            response = await self._request_with_retry(
                method=method,
                url=path,
                headers=request_headers,
                json=json,
                params=params,
            )
            
            duration = time.time() - start_time
            
            # Log response
            if self.config.log_responses:
                logger.info(
                    "Adapter response",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": duration * 1000,
                    }
                )
            
            return response
            
        except HTTPStatusError as e:
            duration = time.time() - start_time
            
            # Log error
            if self.config.log_errors:
                logger.error(
                    "Adapter HTTP error",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": e.response.status_code,
                        "duration_ms": duration * 1000,
                        "error": str(e),
                    },
                    exc_info=True,
                )
            raise
            
        except RequestError as e:
            duration = time.time() - start_time
            
            # Log error
            if self.config.log_errors:
                logger.error(
                    "Adapter request error",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_ms": duration * 1000,
                        "error": str(e),
                    },
                    exc_info=True,
                )
            raise
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Make request with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    params=params,
                )
                
                # Don't retry on client errors (4xx)
                if 400 <= response.status_code < 500:
                    return response
                
                # Retry on server errors (5xx) or network errors
                if response.status_code < 500:
                    return response
                
                # Server error - will retry
                last_exception = HTTPStatusError(
                    f"Server error: {response.status_code}",
                    request=response.request,
                    response=response,
                )
                
            except (RequestError, HTTPStatusError) as e:
                last_exception = e
                
                # Don't retry on client errors
                if isinstance(e, HTTPStatusError) and 400 <= e.response.status_code < 500:
                    raise
                
                # Wait before retry (exponential backoff)
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_backoff_factor * (2 ** attempt)
                    await asyncio.sleep(wait_time)
        
        # All retries exhausted
        raise last_exception
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

