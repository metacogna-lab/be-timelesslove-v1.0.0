"""
Storage endpoint adapters.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from adapters.client import AdapterClient
from adapters.transformers.response import ResponseTransformer
from adapters.transformers.errors import ErrorTransformer
from adapters.middleware.logging import AdapterLogger, RequestTimer
from adapters.middleware.sanitization import Sanitizer
from adapters.config import get_adapter_config

router = APIRouter()
security = HTTPBearer()
logger = AdapterLogger()
config = get_adapter_config()
response_transformer = ResponseTransformer()
error_transformer = ErrorTransformer()
sanitizer = Sanitizer()


class UploadUrlRequest(BaseModel):
    """Upload URL request."""
    memory_id: UUID
    file_name: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=100)


async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header."""
    return credentials.credentials


@router.post("/upload-url")
async def create_upload_url(
    request: UploadUrlRequest,
    token: str = Depends(get_token)
):
    """Get upload URL."""
    request_id = logger.log_request("POST", "/storage/upload-url")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path="/storage/upload-url",
                    token=token,
                    json=validated_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/storage/upload-url", "POST")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("/access-url")
async def create_access_url(
    storage_path: str = Query(..., description="Storage path to the media file"),
    expires_in: Optional[int] = Query(None, description="URL expiration in seconds"),
    token: str = Depends(get_token)
):
    """Get access URL."""
    request_id = logger.log_request("GET", "/storage/access-url")
    timer = RequestTimer()
    
    try:
        with timer:
            params = {
                "storage_path": storage_path,
            }
            if expires_in:
                params["expires_in"] = expires_in
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path="/storage/access-url",
                    token=token,
                    params=params,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/storage/access-url", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("/media/{media_id}/url")
async def get_media_url(
    media_id: UUID,
    expires_in: Optional[int] = Query(None, description="URL expiration in seconds"),
    token: str = Depends(get_token)
):
    """Get media URL by ID."""
    request_id = logger.log_request("GET", f"/storage/media/{media_id}/url")
    timer = RequestTimer()
    
    try:
        with timer:
            params = {}
            if expires_in:
                params["expires_in"] = expires_in
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path=f"/storage/media/{media_id}/url",
                    token=token,
                    params=params,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/storage/media/{media_id}/url", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


# Export adapter instance
storage_adapter = router

