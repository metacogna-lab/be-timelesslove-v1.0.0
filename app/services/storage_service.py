"""
Supabase Storage service for file operations and signed URL generation.
"""

from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from app.db.supabase import get_supabase_service_client
from app.utils.media import validate_storage_path, validate_file_name
from app.config import get_settings


def generate_upload_url(
    family_unit_id: UUID,
    memory_id: UUID,
    file_name: str,
    expires_in: int = 300  # 5 minutes default
) -> str:
    """
    Generate signed URL for uploading to Supabase Storage.
    
    Args:
        family_unit_id: Family unit UUID
        memory_id: Memory UUID
        file_name: Name of the file to upload
        expires_in: URL expiration in seconds (default: 300)
    
    Returns:
        Signed upload URL
    
    Raises:
        HTTPException: If file name is invalid
    """
    # Validate file name
    if not validate_file_name(file_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name"
        )
    
    # Construct storage path
    storage_path = f"{family_unit_id}/{memory_id}/{file_name}"
    
    # Generate signed upload URL
    service_client = get_supabase_service_client()
    
    try:
        # Note: Supabase Python client may have different API for signed URLs
        # This is a placeholder - adjust based on actual Supabase client API
        response = service_client.storage.from_("memories").create_signed_upload_url(
            storage_path,
            expires_in=expires_in
        )
        
        # Extract URL from response (adjust based on actual response format)
        if isinstance(response, dict):
            return response.get("signedUrl") or response.get("url", "")
        elif isinstance(response, str):
            return response
        else:
            raise ValueError("Unexpected response format from Supabase Storage")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


def generate_access_url(
    storage_path: str,
    expires_in: int = 3600  # 1 hour default
) -> str:
    """
    Generate signed URL for accessing media from Supabase Storage.
    
    Args:
        storage_path: Path to file in storage
        expires_in: URL expiration in seconds (default: 3600)
    
    Returns:
        Signed access URL
    
    Raises:
        HTTPException: If storage path is invalid
    """
    # Validate storage path
    if not validate_storage_path(storage_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path"
        )
    
    # Generate signed access URL
    service_client = get_supabase_service_client()
    
    try:
        # Extract bucket and path
        # Path format: {family_unit_id}/{memory_id}/{file_name}
        response = service_client.storage.from_("memories").create_signed_url(
            storage_path,
            expires_in=expires_in
        )
        
        # Extract URL from response (adjust based on actual response format)
        if isinstance(response, dict):
            return response.get("signedUrl") or response.get("url", "")
        elif isinstance(response, str):
            return response
        else:
            raise ValueError("Unexpected response format from Supabase Storage")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate access URL: {str(e)}"
        )


def verify_file_exists(storage_path: str) -> bool:
    """
    Verify that a file exists in Supabase Storage.
    
    Args:
        storage_path: Path to file in storage
    
    Returns:
        True if file exists, False otherwise
    """
    service_client = get_supabase_service_client()
    
    try:
        # List files at the path (or check if file exists)
        # Adjust based on actual Supabase Storage API
        files = service_client.storage.from_("memories").list(
            path=storage_path.rsplit("/", 1)[0] if "/" in storage_path else ""
        )
        
        file_name = storage_path.split("/")[-1]
        
        # Check if file exists in the list
        if isinstance(files, list):
            return any(f.get("name") == file_name for f in files)
        elif isinstance(files, dict):
            return files.get("name") == file_name
        
        return False
        
    except Exception:
        return False


def delete_file(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage.
    
    Args:
        storage_path: Path to file in storage
    
    Returns:
        True if deleted, False otherwise
    """
    service_client = get_supabase_service_client()
    
    try:
        service_client.storage.from_("memories").remove([storage_path])
        return True
    except Exception:
        return False


def get_file_info(storage_path: str) -> Optional[dict]:
    """
    Get file information from Supabase Storage.
    
    Args:
        storage_path: Path to file in storage
    
    Returns:
        File information dict or None if not found
    """
    service_client = get_supabase_service_client()
    
    try:
        # List files to get metadata
        # Adjust based on actual Supabase Storage API
        files = service_client.storage.from_("memories").list(
            path=storage_path.rsplit("/", 1)[0] if "/" in storage_path else ""
        )
        
        file_name = storage_path.split("/")[-1]
        
        if isinstance(files, list):
            for file_info in files:
                if file_info.get("name") == file_name:
                    return file_info
        
        return None
        
    except Exception:
        return None

