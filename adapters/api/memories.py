"""
Memory endpoint adapters.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from adapters.client import AdapterClient
from adapters.transformers.request import RequestTransformer
from adapters.transformers.response import ResponseTransformer
from adapters.transformers.errors import ErrorTransformer
from adapters.validators.schemas import FrontendMemoryRequest
from adapters.middleware.logging import AdapterLogger, RequestTimer
from adapters.middleware.sanitization import Sanitizer
from adapters.config import get_adapter_config

router = APIRouter()
security = HTTPBearer()
logger = AdapterLogger()
config = get_adapter_config()
request_transformer = RequestTransformer()
response_transformer = ResponseTransformer()
error_transformer = ErrorTransformer()
sanitizer = Sanitizer()


async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header."""
    return credentials.credentials


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    request: FrontendMemoryRequest,
    token: str = Depends(get_token)
):
    """Create memory."""
    request_id = logger.log_request("POST", "/memories")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            transformed_data = request_transformer.transform_memory_request(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path="/memories",
                    token=token,
                    json=transformed_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_memory_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/memories", "POST")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("/{memory_id}")
async def get_memory(
    memory_id: UUID,
    token: str = Depends(get_token)
):
    """Get memory by ID."""
    request_id = logger.log_request("GET", f"/memories/{memory_id}")
    timer = RequestTimer()
    
    try:
        with timer:
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path=f"/memories/{memory_id}",
                    token=token,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_memory_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/memories/{memory_id}", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.put("/{memory_id}")
async def update_memory(
    memory_id: UUID,
    request: FrontendMemoryRequest,
    token: str = Depends(get_token)
):
    """Update memory."""
    request_id = logger.log_request("PUT", f"/memories/{memory_id}")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump(exclude_unset=True)
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            transformed_data = request_transformer.transform_memory_request(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="PUT",
                    path=f"/memories/{memory_id}",
                    token=token,
                    json=transformed_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_memory_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/memories/{memory_id}", "PUT")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    token: str = Depends(get_token)
):
    """Delete memory."""
    request_id = logger.log_request("DELETE", f"/memories/{memory_id}")
    timer = RequestTimer()
    
    try:
        with timer:
            async with AdapterClient() as client:
                response = await client.request(
                    method="DELETE",
                    path=f"/memories/{memory_id}",
                    token=token,
                    request_id=request_id,
                )
                response.raise_for_status()
            
            logger.log_response(request_id, status.HTTP_204_NO_CONTENT, timer.duration)
            return None
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/memories/{memory_id}", "DELETE")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("")
async def list_memories(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token: str = Depends(get_token)
):
    """List memories."""
    request_id = logger.log_request("GET", "/memories")
    timer = RequestTimer()
    
    try:
        with timer:
            params = {
                "status": status_filter,
                "page": page,
                "page_size": page_size,
            }
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path="/memories",
                    token=token,
                    params=params,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            # Transform list response
            if isinstance(response_data, list):
                transformed_response = response_transformer.transform_list_response(
                    response_data,
                    item_transformer=response_transformer.transform_memory_response
                )
            else:
                transformed_response = response_data
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_list(transformed_response) if isinstance(transformed_response, list) else sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/memories", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


# Export adapter instance
memories_adapter = router

