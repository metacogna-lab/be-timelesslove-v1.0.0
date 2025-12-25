"""
Memory API endpoints for CRUD operations and media management.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from app.dependencies import get_current_user
from app.dependencies.rbac import exclude_pets, require_content_owner_or_adult, require_content_editor
from app.schemas.memory import (
    CreateMemoryRequest,
    UpdateMemoryRequest,
    MemoryResponse,
    MediaResponse,
    AddMediaRequest
)
from app.services.memory_service import (
    create_memory,
    get_memory_by_id,
    get_memory_with_media,
    update_memory,
    delete_memory,
    create_media,
    get_media_by_memory_id,
    delete_media,
    get_family_memories
)
from app.utils.jwt import TokenClaims
from app.utils.media import is_allowed_mime_type, validate_storage_path
from app.services.storage_service import verify_file_exists
from app.services.media_processor import process_media_async
from app.services.analytics_service import get_analytics_service


router = APIRouter()


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory_endpoint(
    request: CreateMemoryRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenClaims = Depends(get_current_user)
):
    """
    Create a new memory with media references.
    
    Frontend should upload files to Supabase Storage first, then call this endpoint
    with the storage paths.
    """
    # Create memory
    memory = await create_memory(
        user_id=UUID(current_user.sub),
        family_unit_id=UUID(current_user.family_unit_id),
        title=request.title,
        description=request.description,
        memory_date=request.memory_date.isoformat() if request.memory_date else None,
        location=request.location,
        tags=request.tags,
        status=request.status
    )
    
    # Create media records
    media_responses = []
    for media_ref in request.media:
        # Validate storage path
        if not validate_storage_path(media_ref.storage_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid storage path: {media_ref.storage_path}"
            )
        
        # Validate MIME type
        if not is_allowed_mime_type(media_ref.mime_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {media_ref.mime_type}"
            )
        
        # Verify file exists in storage
        if not verify_file_exists(media_ref.storage_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found in storage: {media_ref.storage_path}"
            )
        
        # Create media record
        media = await create_media(
            memory_id=memory.id,
            storage_path=media_ref.storage_path,
            file_name=media_ref.file_name,
            mime_type=media_ref.mime_type,
            file_size=media_ref.file_size
        )
        
        # Queue background processing
        background_tasks.add_task(
            process_media_async,
            media_id=media.id
        )
        
        media_responses.append({
            "id": str(media.id),
            "memory_id": str(media.memory_id),
            "storage_path": media.storage_path,
            "storage_bucket": media.storage_bucket,
            "file_name": media.file_name,
            "mime_type": media.mime_type,
            "file_size": media.file_size,
            "width": media.width,
            "height": media.height,
            "duration": media.duration,
            "thumbnail_path": media.thumbnail_path,
            "processing_status": media.processing_status,
            "created_at": media.created_at.isoformat(),
            "updated_at": media.updated_at.isoformat()
        })
    
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        family_unit_id=memory.family_unit_id,
        title=memory.title,
        description=memory.description,
        memory_date=memory.memory_date.isoformat() if memory.memory_date else None,
        location=memory.location,
        tags=memory.tags,
        status=memory.status,
        created_at=memory.created_at.isoformat(),
        updated_at=memory.updated_at.isoformat(),
        modified_by=memory.modified_by,
        media=media_responses
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID,
    current_user: TokenClaims = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Get memory details with media."""
    memory_with_media = await get_memory_with_media(memory_id)
    
    if not memory_with_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Verify family unit access
    if memory_with_media.family_unit_id != UUID(current_user.family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return MemoryResponse(
        id=memory_with_media.id,
        user_id=memory_with_media.user_id,
        family_unit_id=memory_with_media.family_unit_id,
        title=memory_with_media.title,
        description=memory_with_media.description,
        memory_date=memory_with_media.memory_date.isoformat() if memory_with_media.memory_date else None,
        location=memory_with_media.location,
        tags=memory_with_media.tags,
        status=memory_with_media.status,
        created_at=memory_with_media.created_at.isoformat(),
        updated_at=memory_with_media.updated_at.isoformat(),
        modified_by=memory_with_media.modified_by,
        media=[
            {
                "id": str(m.id),
                "memory_id": str(m.memory_id),
                "storage_path": m.storage_path,
                "storage_bucket": m.storage_bucket,
                "file_name": m.file_name,
                "mime_type": m.mime_type,
                "file_size": m.file_size,
                "width": m.width,
                "height": m.height,
                "duration": m.duration,
                "thumbnail_path": m.thumbnail_path,
                "processing_status": m.processing_status,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat()
            }
            for m in memory_with_media.media
        ]
    )


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory_endpoint(
    memory_id: UUID,
    request: UpdateMemoryRequest,
    current_user: TokenClaims = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Update a memory."""
    # Get existing memory to verify access
    memory = await get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Verify access
    if memory.family_unit_id != UUID(current_user.family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check permission to update (RBAC dependency will handle this)
    # Verify user can edit (owner or adult in family)
    from app.services.rbac import can_edit_content
    is_owner = memory.user_id == UUID(current_user.sub)
    if not can_edit_content(current_user.role, is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this memory"
        )
    
    # Update memory
    updated_memory = await update_memory(
        memory_id=memory_id,
        title=request.title,
        description=request.description,
        memory_date=request.memory_date.isoformat() if request.memory_date else None,
        location=request.location,
        tags=request.tags,
        status=request.status,
        modified_by=UUID(current_user.sub)
    )
    
    if not updated_memory:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory"
        )
    
    # Get media
    media_list = await get_media_by_memory_id(memory_id)
    
    return MemoryResponse(
        id=updated_memory.id,
        user_id=updated_memory.user_id,
        family_unit_id=updated_memory.family_unit_id,
        title=updated_memory.title,
        description=updated_memory.description,
        memory_date=updated_memory.memory_date.isoformat() if updated_memory.memory_date else None,
        location=updated_memory.location,
        tags=updated_memory.tags,
        status=updated_memory.status,
        created_at=updated_memory.created_at.isoformat(),
        updated_at=updated_memory.updated_at.isoformat(),
        modified_by=updated_memory.modified_by,
        media=[
            {
                "id": str(m.id),
                "memory_id": str(m.memory_id),
                "storage_path": m.storage_path,
                "storage_bucket": m.storage_bucket,
                "file_name": m.file_name,
                "mime_type": m.mime_type,
                "file_size": m.file_size,
                "width": m.width,
                "height": m.height,
                "duration": m.duration,
                "thumbnail_path": m.thumbnail_path,
                "processing_status": m.processing_status,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat()
            }
            for m in media_list
        ]
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_endpoint(
    memory_id: UUID,
    current_user: TokenClaims = Depends(get_current_user)
):
    """Delete a memory."""
    # Get existing memory to verify access
    memory = await get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Verify access
    if memory.family_unit_id != UUID(current_user.family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check permission to delete
    from app.services.rbac import can_delete_content
    can_delete = can_delete_content(
        current_user.role,
        is_owner=(memory.user_id == UUID(current_user.sub))
    )
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this memory"
        )
    
    # Delete memory (cascades to media)
    success = await delete_memory(memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )
    
    # Emit analytics event for memory deletion
    background_tasks = BackgroundTasks()
    background_tasks.add_task(
        get_analytics_service().emit_event,
        event_type="memory_deleted",
        user_id=UUID(current_user.sub),
        family_unit_id=UUID(current_user.family_unit_id),
        metadata={
            "memory_id": str(memory_id),
            "deleted_by_owner": memory.user_id == UUID(current_user.sub)
        }
    )


@router.post("/{memory_id}/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def add_media_to_memory(
    memory_id: UUID,
    request: AddMediaRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenClaims = Depends(get_current_user)
):
    """Add media to an existing memory."""
    # Get memory to verify access
    memory = await get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Verify access
    if memory.family_unit_id != UUID(current_user.family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Validate storage path and MIME type
    if not validate_storage_path(request.storage_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path"
        )
    
    if not is_allowed_mime_type(request.mime_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: {request.mime_type}"
        )
    
    # Verify file exists
    if not verify_file_exists(request.storage_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found in storage"
        )
    
    # Create media record
    media = await create_media(
        memory_id=memory_id,
        storage_path=request.storage_path,
        file_name=request.file_name,
        mime_type=request.mime_type,
        file_size=request.file_size
    )
    
    # Queue background processing
    background_tasks.add_task(
        process_media_async,
        media_id=media.id
    )
    
    return MediaResponse(
        id=media.id,
        memory_id=media.memory_id,
        storage_path=media.storage_path,
        storage_bucket=media.storage_bucket,
        file_name=media.file_name,
        mime_type=media.mime_type,
        file_size=media.file_size,
        width=media.width,
        height=media.height,
        duration=media.duration,
        thumbnail_path=media.thumbnail_path,
        processing_status=media.processing_status,
        created_at=media.created_at.isoformat(),
        updated_at=media.updated_at.isoformat()
    )


@router.delete("/{memory_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_media_from_memory(
    memory_id: UUID,
    media_id: UUID,
    current_user: TokenClaims = Depends(get_current_user)
):
    """Remove media from a memory."""
    # Get memory to verify access
    memory = await get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Verify access
    if memory.family_unit_id != UUID(current_user.family_unit_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get media to verify it belongs to memory
    from app.services.memory_service import get_media_by_id
    media = await get_media_by_id(media_id)
    if not media or media.memory_id != memory_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Delete media
    success = await delete_media(media_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media"
        )


@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: TokenClaims = Depends(get_current_user)
):
    """List memories for the user's family unit."""
    memories = await get_family_memories(
        family_unit_id=UUID(current_user.family_unit_id),
        limit=limit,
        offset=offset,
        status=status_filter
    )
    
    return [
        MemoryResponse(
            id=m.id,
            user_id=m.user_id,
            family_unit_id=m.family_unit_id,
            title=m.title,
            description=m.description,
            memory_date=m.memory_date.isoformat() if m.memory_date else None,
            location=m.location,
            tags=m.tags,
            status=m.status,
            created_at=m.created_at.isoformat(),
            updated_at=m.updated_at.isoformat(),
            modified_by=m.modified_by,
            media=[]  # Media loaded separately if needed
        )
        for m in memories
    ]

