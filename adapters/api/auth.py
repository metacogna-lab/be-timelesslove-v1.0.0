"""
Authentication endpoint adapters.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from adapters.client import AdapterClient
from adapters.transformers.request import RequestTransformer
from adapters.transformers.response import ResponseTransformer
from adapters.transformers.errors import ErrorTransformer
from adapters.validators.schemas import FrontendAuthRequest
from adapters.middleware.logging import AdapterLogger, RequestTimer
from adapters.middleware.sanitization import Sanitizer
from adapters.config import get_adapter_config

router = APIRouter()
security = HTTPBearer(auto_error=False)
logger = AdapterLogger()
config = get_adapter_config()
request_transformer = RequestTransformer()
response_transformer = ResponseTransformer()
error_transformer = ErrorTransformer()
sanitizer = Sanitizer()


async def get_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Extract token from Authorization header."""
    if credentials:
        return credentials.credentials
    return None


@router.post("/register/adult", status_code=status.HTTP_201_CREATED)
async def register_adult(
    request: FrontendAuthRequest,
    token: Optional[str] = Depends(get_token)
):
    """Register adult user."""
    request_id = logger.log_request("POST", "/register/adult")
    timer = RequestTimer()
    
    try:
        with timer:
            # Validate request
            validated_data = request.model_dump()
            
            # Sanitize input
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            # Transform request
            transformed_data = request_transformer.transform_auth_request(validated_data)
            
            # Call backend
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path="/auth/register/adult",
                    json=transformed_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            # Transform response
            transformed_response = response_transformer.transform_auth_response(response_data)
            
            # Sanitize output
            if config.sanitize_outputs:
                transformed_response = sanitizer.remove_sensitive_data(transformed_response)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/register/adult", "POST")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response["error"]
        )


@router.post("/register/teen", status_code=status.HTTP_201_CREATED)
async def register_teen(
    request: FrontendAuthRequest,
    token: Optional[str] = Depends(get_token)
):
    """Register teen user."""
    request_id = logger.log_request("POST", "/register/teen")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            transformed_data = request_transformer.transform_auth_request(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path="/auth/register/teen",
                    json=transformed_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_auth_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.remove_sensitive_data(transformed_response)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/register/teen", "POST")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response["error"]
        )


@router.post("/register/grandparent", status_code=status.HTTP_201_CREATED)
async def register_grandparent(
    request: FrontendAuthRequest,
    token: Optional[str] = Depends(get_token)
):
    """Register grandparent user."""
    request_id = logger.log_request("POST", "/register/grandparent")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            transformed_data = request_transformer.transform_auth_request(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path="/auth/register/grandparent",
                    json=transformed_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_auth_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.remove_sensitive_data(transformed_response)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/register/grandparent", "POST")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response["error"]
        )


# Export adapter instance
auth_adapter = router

