"""
Feed endpoint adapters.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from adapters.client import AdapterClient
from adapters.transformers.request import RequestTransformer
from adapters.transformers.response import ResponseTransformer
from adapters.transformers.errors import ErrorTransformer
from adapters.validators.schemas import FrontendFeedFilters, FrontendReactionRequest, FrontendCommentRequest
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


@router.get("")
async def get_feed(
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    order_by: str = Query("feed_score"),
    order_direction: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    memory_date_from: Optional[str] = Query(None),
    memory_date_to: Optional[str] = Query(None),
    token: str = Depends(get_token)
):
    """Get feed."""
    request_id = logger.log_request("GET", "/feed")
    timer = RequestTimer()
    
    try:
        with timer:
            # Build filter params
            filter_params = {
                "status": status,
                "user_id": user_id,
                "tags": tags,
                "search_query": search_query,
                "order_by": order_by,
                "order_direction": order_direction,
                "page": page,
                "page_size": page_size,
                "memory_date_from": memory_date_from,
                "memory_date_to": memory_date_to,
            }
            
            # Transform filters
            transformed_params = request_transformer.transform_feed_filters(filter_params)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path="/feed",
                    token=token,
                    params=transformed_params,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_feed_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/feed", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.post("/memories/{memory_id}/reactions", status_code=status.HTTP_201_CREATED)
async def create_reaction(
    memory_id: UUID,
    request: FrontendReactionRequest,
    token: str = Depends(get_token)
):
    """Create reaction."""
    request_id = logger.log_request("POST", f"/feed/memories/{memory_id}/reactions")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path=f"/feed/memories/{memory_id}/reactions",
                    token=token,
                    json=validated_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/feed/memories/{memory_id}/reactions", "POST")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.delete("/memories/{memory_id}/reactions/{reaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(
    memory_id: UUID,
    reaction_id: UUID,
    token: str = Depends(get_token)
):
    """Delete reaction."""
    request_id = logger.log_request("DELETE", f"/feed/memories/{memory_id}/reactions/{reaction_id}")
    timer = RequestTimer()
    
    try:
        with timer:
            async with AdapterClient() as client:
                response = await client.request(
                    method="DELETE",
                    path=f"/feed/memories/{memory_id}/reactions/{reaction_id}",
                    token=token,
                    request_id=request_id,
                )
                response.raise_for_status()
            
            logger.log_response(request_id, status.HTTP_204_NO_CONTENT, timer.duration)
            return None
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/feed/memories/{memory_id}/reactions/{reaction_id}", "DELETE")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("/memories/{memory_id}/reactions")
async def get_reactions(
    memory_id: UUID,
    token: str = Depends(get_token)
):
    """Get reactions for memory."""
    request_id = logger.log_request("GET", f"/feed/memories/{memory_id}/reactions")
    timer = RequestTimer()
    
    try:
        with timer:
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path=f"/feed/memories/{memory_id}/reactions",
                    token=token,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_list(response_data) if isinstance(response_data, list) else sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/feed/memories/{memory_id}/reactions", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.post("/memories/{memory_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(
    memory_id: UUID,
    request: FrontendCommentRequest,
    token: str = Depends(get_token)
):
    """Create comment."""
    request_id = logger.log_request("POST", f"/feed/memories/{memory_id}/comments")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path=f"/feed/memories/{memory_id}/comments",
                    token=token,
                    json=validated_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/feed/memories/{memory_id}/comments", "POST")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("/memories/{memory_id}/comments")
async def get_comments(
    memory_id: UUID,
    include_replies: bool = Query(True),
    limit: Optional[int] = Query(None),
    token: str = Depends(get_token)
):
    """Get comments for memory."""
    request_id = logger.log_request("GET", f"/feed/memories/{memory_id}/comments")
    timer = RequestTimer()
    
    try:
        with timer:
            params = {
                "include_replies": include_replies,
            }
            if limit:
                params["limit"] = limit
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path=f"/feed/memories/{memory_id}/comments",
                    token=token,
                    params=params,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_list(response_data) if isinstance(response_data, list) else sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/feed/memories/{memory_id}/comments", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


# Export adapter instance
feed_adapter = router

