"""
Invitation endpoint adapters.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

from adapters.client import AdapterClient
from adapters.transformers.request import RequestTransformer
from adapters.transformers.response import ResponseTransformer
from adapters.transformers.errors import ErrorTransformer
from adapters.validators.schemas import FrontendInviteRequest
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


class AcceptInviteRequest(BaseModel):
    """Accept invitation request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)


async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header."""
    return credentials.credentials


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_invite(
    request: FrontendInviteRequest,
    token: str = Depends(get_token)
):
    """Create invitation."""
    request_id = logger.log_request("POST", "/invites")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            transformed_data = request_transformer.transform_invite_request(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path="/invites",
                    token=token,
                    json=transformed_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_invite_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_201_CREATED, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, "/invites", "POST")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.get("/{token}")
async def validate_invite(
    token: str
):
    """Validate invitation token."""
    request_id = logger.log_request("GET", f"/invites/{token}")
    timer = RequestTimer()
    
    try:
        with timer:
            async with AdapterClient() as client:
                response = await client.request(
                    method="GET",
                    path=f"/invites/{token}",
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            # Transform response if invite is present
            if "invite" in response_data and response_data["invite"]:
                response_data["invite"] = response_transformer.transform_invite_response(
                    response_data["invite"]
                )
            
            if config.sanitize_outputs:
                response_data = sanitizer.sanitize_dict(response_data)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return response_data
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/invites/{token}", "GET")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


@router.post("/{token}/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    token: str,
    request: AcceptInviteRequest
):
    """Accept invitation."""
    request_id = logger.log_request("POST", f"/invites/{token}/accept")
    timer = RequestTimer()
    
    try:
        with timer:
            validated_data = request.model_dump()
            
            if config.sanitize_inputs:
                validated_data = sanitizer.sanitize_dict(validated_data)
            
            async with AdapterClient() as client:
                response = await client.request(
                    method="POST",
                    path=f"/invites/{token}/accept",
                    json=validated_data,
                    request_id=request_id,
                )
                response.raise_for_status()
                response_data = response.json()
            
            transformed_response = response_transformer.transform_invite_response(response_data)
            
            if config.sanitize_outputs:
                transformed_response = sanitizer.sanitize_dict(transformed_response)
            
            logger.log_response(request_id, status.HTTP_200_OK, timer.duration)
            return transformed_response
            
    except Exception as e:
        logger.log_error(request_id, e)
        error_response = error_transformer.transform_error(e, f"/invites/{token}/accept", "POST")
        status_code = error_response["error"].get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=error_response["error"])


# Export adapter instance
invites_adapter = router

