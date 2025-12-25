"""
Storage API endpoints for signed URL generation.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_current_user
from app.schemas.memory import UploadUrlRequest, UploadUrlResponse, AccessUrlResponse
from app.services.storage_service import generate_upload_url, generate_access_url
from app.utils.jwt import TokenClaims
from app.utils.media import validate_file_name, is_allowed_mime_type
from app.config import get_settings


router = APIRouter()
settings = get_settings()


@router.post("/upload-url", response_model=UploadUrlResponse)
async def create_upload_url(
    request: UploadUrlRequest,
    current_user: TokenClaims = Depends(get_current_user)
):
    """
    Generate signed URL for uploading media to Supabase Storage.
    
    The frontend will use this URL to upload files directly to Supabase Storage,
    then call the memory registration endpoint with the storage path.
    """
    # Validate file name
    if not validate_file_name(request.file_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name"
        )
    
    # Validate MIME type
    if not is_allowed_mime_type(request.mime_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: {request.mime_type}"
        )
    
    # Generate upload URL
    try:
        upload_url = generate_upload_url(
            family_unit_id=UUID(current_user.family_unit_id),
            memory_id=request.memory_id,
            file_name=request.file_name,
            expires_in=settings.media_upload_url_expires_seconds
        )
        
        # Construct storage path for reference
        storage_path = f"{current_user.family_unit_id}/{request.memory_id}/{request.file_name}"
        
        return UploadUrlResponse(
            upload_url=upload_url,
            storage_path=storage_path,
            expires_in=settings.media_upload_url_expires_seconds
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.get("/access-url", response_model=AccessUrlResponse)
async def create_access_url(
    storage_path: str = Query(..., description="Storage path to the media file"),
    expires_in: Optional[int] = Query(None, description="URL expiration in seconds"),
    current_user: TokenClaims = Depends(get_current_user)
):
    """
    Generate signed URL for accessing media from Supabase Storage.
    
    Used to retrieve media files with time-limited access.
    """
    # Validate storage path belongs to user's family unit
    path_parts = storage_path.split("/")
    if len(path_parts) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path format"
        )
    
    family_unit_id = path_parts[0]
    if family_unit_id != current_user.family_unit_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Storage path does not belong to your family unit"
        )
    
    # Generate access URL
    try:
        url_expires_in = expires_in or settings.media_access_url_expires_seconds
        access_url = generate_access_url(
            storage_path=storage_path,
            expires_in=url_expires_in
        )
        
        return AccessUrlResponse(
            access_url=access_url,
            expires_in=url_expires_in
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate access URL: {str(e)}"
        )


@router.get("/media/{media_id}/url", response_model=AccessUrlResponse)
async def get_media_url(
    media_id: UUID,
    expires_in: Optional[int] = Query(None, description="URL expiration in seconds"),
    current_user: TokenClaims = Depends(get_current_user)
):
    """
    Get signed URL for a specific media file by media ID.
    
    Fetches the media record and generates a signed URL for access.
    """
    from app.services.memory_service import get_media_by_id
    
    # Get media record
    media = await get_media_by_id(media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Verify user has access (via memory's family unit)
    from app.services.memory_service import get_memory_by_id
    memory = await get_memory_by_id(media.memory_id)
    if not memory or memory.family_unit_id != UUID(current_user.family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Generate access URL
    try:
        url_expires_in = expires_in or settings.media_access_url_expires_seconds
        access_url = generate_access_url(
            storage_path=media.storage_path,
            expires_in=url_expires_in
        )
        
        return AccessUrlResponse(
            access_url=access_url,
            expires_in=url_expires_in
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate access URL: {str(e)}"
        )

