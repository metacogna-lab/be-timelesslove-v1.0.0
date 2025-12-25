"""
Memory service for memory and media operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from supabase import Client
from app.db.supabase import get_supabase_service_client
from app.models.memory import Memory, MemoryMedia, MemoryWithMedia
from app.services.storage_service import verify_file_exists


async def create_memory(
    user_id: UUID,
    family_unit_id: UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    memory_date: Optional[str] = None,
    location: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: str = "draft"
) -> Memory:
    """
    Create a new memory.
    
    Args:
        user_id: User UUID creating the memory
        family_unit_id: Family unit UUID
        title: Memory title
        description: Memory description
        memory_date: Date when memory occurred
        location: Location of memory
        tags: List of tags
        status: Memory status (draft, published, archived)
    
    Returns:
        Created Memory
    """
    service_client = get_supabase_service_client()
    
    memory_data = {
        "user_id": str(user_id),
        "family_unit_id": str(family_unit_id),
        "title": title,
        "description": description,
        "memory_date": memory_date.isoformat() if memory_date and hasattr(memory_date, 'isoformat') else memory_date,
        "location": location,
        "tags": tags or [],
        "status": status
    }
    
    result = service_client.table("memories").insert(memory_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create memory")
    
    return Memory(**result.data[0])


async def get_memory_by_id(memory_id: UUID) -> Optional[Memory]:
    """
    Get memory by ID.
    
    Args:
        memory_id: Memory UUID
    
    Returns:
        Memory if found, None otherwise
    """
    service_client = get_supabase_service_client()
    
    result = service_client.table("memories").select("*").eq(
        "id", str(memory_id)
    ).single().execute()
    
    if not result.data:
        return None
    
    return Memory(**result.data)


async def get_memory_with_media(memory_id: UUID) -> Optional[MemoryWithMedia]:
    """
    Get memory with associated media.
    
    Args:
        memory_id: Memory UUID
    
    Returns:
        MemoryWithMedia if found, None otherwise
    """
    memory = await get_memory_by_id(memory_id)
    if not memory:
        return None
    
    # Get media
    media_list = await get_media_by_memory_id(memory_id)
    
    return MemoryWithMedia(
        **memory.model_dump(),
        media=media_list
    )


async def update_memory(
    memory_id: UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    memory_date: Optional[str] = None,
    location: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    modified_by: Optional[UUID] = None
) -> Optional[Memory]:
    """
    Update a memory.
    
    Args:
        memory_id: Memory UUID
        title: New title
        description: New description
        memory_date: New memory date
        location: New location
        tags: New tags
        status: New status
        modified_by: User UUID who modified
    
    Returns:
        Updated Memory if found, None otherwise
    """
    service_client = get_supabase_service_client()
    
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if memory_date is not None:
        if hasattr(memory_date, 'isoformat'):
            update_data["memory_date"] = memory_date.isoformat()
        else:
            update_data["memory_date"] = memory_date
    if location is not None:
        update_data["location"] = location
    if tags is not None:
        update_data["tags"] = tags
    if status is not None:
        update_data["status"] = status
    if modified_by is not None:
        update_data["modified_by"] = str(modified_by)
    
    if not update_data:
        return await get_memory_by_id(memory_id)
    
    result = service_client.table("memories").update(update_data).eq(
        "id", str(memory_id)
    ).execute()
    
    if not result.data:
        return None
    
    return Memory(**result.data[0])


async def delete_memory(memory_id: UUID) -> bool:
    """
    Delete a memory (cascades to media).
    
    Args:
        memory_id: Memory UUID
    
    Returns:
        True if deleted, False otherwise
    """
    service_client = get_supabase_service_client()
    
    try:
        service_client.table("memories").delete().eq("id", str(memory_id)).execute()
        return True
    except Exception:
        return False


async def create_media(
    memory_id: UUID,
    storage_path: str,
    file_name: str,
    mime_type: str,
    file_size: int,
    storage_bucket: str = "memories"
) -> MemoryMedia:
    """
    Create a media record.
    
    Args:
        memory_id: Memory UUID
        storage_path: Path in Supabase Storage
        file_name: Original file name
        mime_type: MIME type
        file_size: File size in bytes
        storage_bucket: Storage bucket name
    
    Returns:
        Created MemoryMedia
    """
    service_client = get_supabase_service_client()
    
    # Verify file exists in storage
    if not verify_file_exists(storage_path):
        raise ValueError(f"File not found in storage: {storage_path}")
    
    media_data = {
        "memory_id": str(memory_id),
        "storage_path": storage_path,
        "storage_bucket": storage_bucket,
        "file_name": file_name,
        "mime_type": mime_type,
        "file_size": file_size,
        "processing_status": "pending"
    }
    
    result = service_client.table("memory_media").insert(media_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create media record")
    
    return MemoryMedia(**result.data[0])


async def get_media_by_id(media_id: UUID) -> Optional[MemoryMedia]:
    """
    Get media by ID.
    
    Args:
        media_id: Media UUID
    
    Returns:
        MemoryMedia if found, None otherwise
    """
    service_client = get_supabase_service_client()
    
    result = service_client.table("memory_media").select("*").eq(
        "id", str(media_id)
    ).single().execute()
    
    if not result.data:
        return None
    
    return MemoryMedia(**result.data)


async def get_media_by_memory_id(memory_id: UUID) -> List[MemoryMedia]:
    """
    Get all media for a memory.
    
    Args:
        memory_id: Memory UUID
    
    Returns:
        List of MemoryMedia
    """
    service_client = get_supabase_service_client()
    
    result = service_client.table("memory_media").select("*").eq(
        "memory_id", str(memory_id)
    ).execute()
    
    if not result.data:
        return []
    
    return [MemoryMedia(**item) for item in result.data]


async def delete_media(media_id: UUID) -> bool:
    """
    Delete a media record.
    
    Args:
        media_id: Media UUID
    
    Returns:
        True if deleted, False otherwise
    """
    service_client = get_supabase_service_client()
    
    try:
        service_client.table("memory_media").delete().eq("id", str(media_id)).execute()
        return True
    except Exception:
        return False


async def update_media_processing_status(
    media_id: UUID,
    status: str,
    thumbnail_path: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    duration: Optional[int] = None,
    metadata: Optional[dict] = None
) -> Optional[MemoryMedia]:
    """
    Update media processing status and metadata.
    
    Args:
        media_id: Media UUID
        status: Processing status
        thumbnail_path: Path to thumbnail
        width: Image/video width
        height: Image/video height
        duration: Video duration
        metadata: Additional metadata
    
    Returns:
        Updated MemoryMedia if found, None otherwise
    """
    service_client = get_supabase_service_client()
    
    update_data = {
        "processing_status": status
    }
    
    if thumbnail_path is not None:
        update_data["thumbnail_path"] = thumbnail_path
    if width is not None:
        update_data["width"] = width
    if height is not None:
        update_data["height"] = height
    if duration is not None:
        update_data["duration"] = duration
    if metadata is not None:
        update_data["metadata"] = metadata
    
    result = service_client.table("memory_media").update(update_data).eq(
        "id", str(media_id)
    ).execute()
    
    if not result.data:
        return None
    
    return MemoryMedia(**result.data[0])


async def get_family_memories(
    family_unit_id: UUID,
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None
) -> List[Memory]:
    """
    Get memories for a family unit.
    
    Args:
        family_unit_id: Family unit UUID
        limit: Maximum number of results
        offset: Offset for pagination
        status: Filter by status (optional)
    
    Returns:
        List of Memory
    """
    service_client = get_supabase_service_client()
    
    query = service_client.table("memories").select("*").eq(
        "family_unit_id", str(family_unit_id)
    )
    
    if status:
        query = query.eq("status", status)
    
    query = query.order("created_at", desc=True).limit(limit).offset(offset)
    
    result = query.execute()
    
    if not result.data:
        return []
    
    return [Memory(**item) for item in result.data]


class MemoryService:
    """Service class for memory operations."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
    
    async def create_memory(self, *args, **kwargs):
        return await create_memory(*args, **kwargs)
    
    async def get_memory_by_id(self, *args, **kwargs):
        return await get_memory_by_id(*args, **kwargs)
    
    async def get_memory_with_media(self, *args, **kwargs):
        return await get_memory_with_media(*args, **kwargs)
    
    async def update_memory(self, *args, **kwargs):
        return await update_memory(*args, **kwargs)
    
    async def delete_memory(self, *args, **kwargs):
        return await delete_memory(*args, **kwargs)
    
    async def create_media(self, *args, **kwargs):
        return await create_media(*args, **kwargs)
    
    async def get_media_by_id(self, *args, **kwargs):
        return await get_media_by_id(*args, **kwargs)
    
    async def get_media_by_memory_id(self, *args, **kwargs):
        return await get_media_by_memory_id(*args, **kwargs)
    
    async def delete_media(self, *args, **kwargs):
        return await delete_media(*args, **kwargs)
    
    async def update_media_processing_status(self, *args, **kwargs):
        return await update_media_processing_status(*args, **kwargs)
    
    async def get_family_memories(self, *args, **kwargs):
        return await get_family_memories(*args, **kwargs)
